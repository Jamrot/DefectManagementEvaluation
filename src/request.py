from email.mime import message
import os
import re
import json
import math
import time
import openai
import random
import logging
import tiktoken
import multiprocessing as mp
import numpy as np
import argparse
import aiohttp
import asyncio  # for running API calls concurrently
from dataclasses import dataclass, field  # for storing API inputs, outputs, and metadata
import shutil
import os

from tqdm import tqdm
from nltk.corpus import stopwords
from openai.error import APIConnectionError, RateLimitError, Timeout, InvalidRequestError, AuthenticationError

import prompt

logger = logging.getLogger(__name__)
time_tag = time.strftime("%m%d%H%M", time.localtime())

def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        # print("Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4":
        # print("Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314.")
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    elif 'gpt-3.5' in model:
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens

async def async_api_requests(
    max_requests_per_minute: float,
    max_tokens_per_minute: float,
    request_url: str,
    api_key: str, 
    root_path:str,
    result_file_path: str, 
    result_file_name: str, 
    task: str,
    dataset: str, 
    model: str ='gpt-3.5-turbo', 
    dataNum: int =0, 
    testNum: int =1, 
    method: str ='base', 
    max_token: int =8000, 
    max_attempts: int =10,
    temperature: float = 0,
    choices: int = 1,
    data = None, 
    ):
    """Processes API requests in parallel, throttling to stay under rate limits."""
    # constants
    seconds_to_pause_after_rate_limit_error = 15
    seconds_to_sleep_each_loop = 0.01  # 1 ms limits max throughput to 1,000 requests per second

    # infer API endpoint and construct request header
    request_header = {"Authorization": f"Bearer {api_key}"}

    # initialize trackers
    queue_of_requests_to_retry = asyncio.Queue()
    status_tracker = StatusTracker()  # single instance to track a collection of variables
    next_request = None  # variable to hold the next request to call

    # initialize available capacity counts
    available_request_capacity = max_requests_per_minute
    available_token_capacity = max_tokens_per_minute
    last_update_time = time.time()

    # initialize flags
    not_finished = True
    
    # initialize file path
    if not os.path.exists(result_file_path):
        os.makedirs(result_file_path)
    results_json_file = os.path.join(result_file_path, result_file_name + ".json")

    """read results from json file"""
    print(results_json_file)
    try:
        with open(results_json_file) as f:
            results_list = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        results_list = []

    """config logging file"""
    logging_level = 'WARNING'
    logging.basicConfig(format='%(asctime)s %(message)s', filename=os.path.join(result_file_path, result_file_name+".log"), encoding='utf-8', level=logging_level)
    logging.debug(f"Logging initialized at level {logging_level}")
    logging.debug(f"Initialization complete.")

    """call openai"""
    openai.api_key = api_key
    testNum = min(testNum, len(data))
    global pbar
    pbar = tqdm(total = testNum-dataNum) 
    while(True):
        # get next request (if one is not already waiting for capacity)
        if next_request is None:
            if not queue_of_requests_to_retry.empty(): 
                next_request = queue_of_requests_to_retry.get_nowait()
                logging.debug(f"Retrying request {next_request.request_id}: {next_request}")
            elif (not_finished):
                if dataNum<testNum:                    
                    request_id = data[dataNum]['id']
                    messages = data[dataNum]['prompt']
                    request_truth = data[dataNum]['ground_truth']
                    
                    request_json = {
                        "model":model,
                        "messages":messages,
                        "temperature":temperature,
                        "top_p":1,
                        "n":choices,
                        "stream":False,
                        "stop":'',
                        # "max_tokens":1000,
                        "logit_bias":{},
                        "presence_penalty":0,
                        "frequency_penalty":0,
                    }
                    next_request = APIRequest(
                        request_id=request_id,
                        request_json=request_json,
                        request_truth=request_truth,
                        token_consumption=num_tokens_from_messages(messages, model),
                        attempts_left=max_attempts,
                        metadata=request_json.pop("metadata", None),
                        results_list=results_list,
                    )
                    status_tracker.num_tasks_started += 1
                    status_tracker.num_tasks_in_progress += 1
                    logging.debug(f"Reading request {next_request.request_id}: {next_request}")
                    dataNum += 1
                    
                else:
                    # if file runs out, set flag to stop reading it
                    logging.debug("Read file exhausted")
                    not_finished = False

        # update available capacity
        current_time = time.time()
        seconds_since_update = current_time - last_update_time
        available_request_capacity = min(
            available_request_capacity + max_requests_per_minute * seconds_since_update / 60.0,
            max_requests_per_minute,
        )
        available_token_capacity = min(
            available_token_capacity + max_tokens_per_minute * seconds_since_update / 60.0,
            max_tokens_per_minute,
        )
        last_update_time = current_time

        # if enough capacity available, call API
        if next_request:
            next_request_tokens = next_request.token_consumption
            if (
                available_request_capacity >= 1
                and available_token_capacity >= next_request_tokens
            ):
                # update counters
                available_request_capacity -= 1
                available_token_capacity -= next_request_tokens
                next_request.attempts_left -= 1

                # call API
                asyncio.create_task(
                    next_request.call_api(
                        request_url=request_url,
                        request_header=request_header,
                        retry_queue=queue_of_requests_to_retry,
                        save_filepath=results_json_file,
                        status_tracker=status_tracker,
                    )
                )
                next_request = None  # reset next_request to empty

        # if all tasks are finished, break
        if status_tracker.num_tasks_in_progress == 0:
            break

        # main loop sleeps briefly so concurrent tasks can run
        await asyncio.sleep(seconds_to_sleep_each_loop)

        # if a rate limit error was hit recently, pause to cool down
        seconds_since_rate_limit_error = (time.time() - status_tracker.time_of_last_rate_limit_error)
        if seconds_since_rate_limit_error < seconds_to_pause_after_rate_limit_error:
            remaining_seconds_to_pause = (seconds_to_pause_after_rate_limit_error - seconds_since_rate_limit_error)
            await asyncio.sleep(remaining_seconds_to_pause)
            # ^e.g., if pause is 15 seconds and final limit was hit 5 seconds ago
            logging.warning(f"Pausing to cool down until {time.ctime(status_tracker.time_of_last_rate_limit_error + seconds_to_pause_after_rate_limit_error)}")

    # after finishing, log final status
    logging.info(f"""Parallel processing complete. Results saved to {results_json_file}""")
    if status_tracker.num_tasks_failed > 0:
        logging.warning(f"{status_tracker.num_tasks_failed} / {status_tracker.num_tasks_started} requests failed. Errors logged to {results_json_file}.")
    if status_tracker.num_rate_limit_errors > 0:
        logging.warning(f"{status_tracker.num_rate_limit_errors} rate limit errors received. Consider running at a lower rate.")

@dataclass
class StatusTracker:
    """Stores metadata about the script's progress. Only one instance is created."""
    num_tasks_started: int = 0
    num_tasks_in_progress: int = 0  # script ends when this reaches 0
    num_tasks_succeeded: int = 0
    num_tasks_failed: int = 0
    num_rate_limit_errors: int = 0
    num_api_errors: int = 0  # excluding rate limit errors, counted above
    num_other_errors: int = 0
    time_of_last_rate_limit_error: int = 0  # used to cool off after hitting rate limits

@dataclass
class APIRequest:
    """Stores an API request's inputs, outputs, and other metadata. Contains a method to make an API call."""

    request_id: int
    request_json: dict
    request_truth: str
    token_consumption: int
    attempts_left: int
    metadata: dict
    results_list: list
    result: list = field(default_factory=list)
    

    async def call_api(
        self,
        request_url: str,
        request_header: dict,
        retry_queue: asyncio.Queue,
        save_filepath: str,
        status_tracker: StatusTracker,
    ):
        """Calls the OpenAI API and saves results."""
        logging.info(f"Starting request #{self.request_id}")
        error = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=request_url, headers=request_header, json=self.request_json
                ) as response:
                    response = await response.json()
            if "error" in response:
                logging.warning(
                    f"Request {self.request_id} failed with error {response['error']}"
                )
                status_tracker.num_api_errors += 1
                error = response
                if "Rate limit" in response["error"].get("message", ""):
                    status_tracker.time_of_last_rate_limit_error = time.time()
                    status_tracker.num_rate_limit_errors += 1
                    status_tracker.num_api_errors -= 1  # rate limit errors are counted separately

        except Exception as e:  # catching naked exceptions is bad practice, but in this case we'll log & save them
            logging.warning(f"Request {self.request_id} failed with Exception {e}")
            status_tracker.num_other_errors += 1
            error = e
        if error:
            self.result.append(error)
            if self.attempts_left:
                retry_queue.put_nowait(self)
            else:
                logging.error(f"Request {self.request_json} failed after all attempts. Saving errors: {self.result}")
                data = (
                    [self.request_json, [str(e) for e in self.result], self.metadata]
                    if self.metadata
                    else [self.request_json, [str(e) for e in self.result]]
                )
                # print(data)
                result = {'id': self.request_id, 'ground_truth':self.request_truth, 'prompt': self.request_json, 'response':response}
                self.results_list.append(result)
                write_file(self.results_list, save_filepath)
                status_tracker.num_tasks_in_progress -= 1
                status_tracker.num_tasks_failed += 1
        else:
            data = (
                [self.request_json, response, self.metadata]
                if self.metadata
                else [self.request_json, response]
            )
            # print(data)
            result = {'id': self.request_id, 'ground_truth':self.request_truth, 'prompt': self.request_json, 'response':response}
            self.results_list.append(result)
            write_file(self.results_list, save_filepath)
            status_tracker.num_tasks_in_progress -= 1
            status_tracker.num_tasks_succeeded += 1
            logging.debug(f"Request {self.request_id} saved to {save_filepath}")
            pbar.update(1)

def write_file(results_list, results_json_file):
    backup_path = results_json_file + '.backup'
    if os.path.exists(results_json_file):
        shutil.copy(results_json_file, backup_path)
    with open(results_json_file, "w+") as f:
        json.dump(results_list, f)
