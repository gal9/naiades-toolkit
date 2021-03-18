from abc import ABC, abstractmethod
from typing import Any, Dict, List
import json
import csv
import os
import datetime

from kafka import KafkaProducer


class Output(ABC):
    from_hour: Any
    to_hour: Any
    field_names: List[str]

    @abstractmethod
    def configure(self, conf: Dict[Any, Any]) -> None:
        # Filed names
        self.field_names = conf["field_names"]

        # Filtering to hours in day
        if("from_hour" in conf and "to_hour" in conf):
            self.from_hour = eval(conf["from_hour"])
            self.to_hour = eval(conf["to_hour"])
        else:
            self.from_hour = None
            self.to_hour = None

    @abstractmethod
    def send_out(self, output_dict: Dict[str, Any],
                 datetime_timestamp: Any) -> None:
        pass

    def time_in_range(self, x: Any) -> bool:
        # Return true if x (in datetime.datetime fomat) is in the range [start, end]
        x = x.time()

        if self.from_hour <= self.to_hour:
            return self.from_hour <= x <= self.to_hour
        else:
            return self.from_hour <= x or x <= self.to_hour

class KafkaOutput(Output):
    # An output class that outputs a dictionary to a kafka topic

    producer: Any
    topic: str
    bootstrap_server: str

    def configure(self, conf: Dict[Any, Any]) -> None:
        self.topic = conf["topic"]
        self.bootstrap_server = conf["bootstrap_server"]

        # Initializes kafka producer with specified server
        self.producer = KafkaProducer(bootstrap_servers=
                                      [self.bootstrap_server],
                                      value_serializer=lambda x:
                                      json.dumps(x).encode('utf-8'))

        super().configure(conf=conf)

    def send_out(self, output_dict: Dict[str, Any],
                 datetime_timestamp: Any) -> None:
        # Execute the send out if time is in range (if that is required)
        if(self.from_hour is None or self.to_hour is None or self.time_in_range(datetime_timestamp)):
            # A method that sends (a dictionary) out a message to the topic
            self.producer.send(self.topic, value=output_dict)


class TerminalOutput(Output):
    # An output class that outputs a dictionary to the terminal

    def configure(self, conf: Dict[Any, Any]) -> None:
        super().configure(conf=conf)

    def send_out(self, output_dict: Dict[str, Any],
                 datetime_timestamp: Any) -> None:
        # Execute the send out if time is in range (if that is required)
        if(self.from_hour is None or self.to_hour is None or self.time_in_range(datetime_timestamp)):
            print(output_dict)


class FileOutput(Output):
    file_name: str
    file_path: str
    mode: str

    def __init__(self, conf: Dict[Any, Any] = None) -> None:
        super().__init__()
        if(conf is not None):
            self.configure(conf=conf)

    def configure(self, conf: Dict[Any, Any] = None) -> None:
        super().configure(conf=conf)
        self.file_name = conf["file_name"]
        self.mode = conf["mode"]
        self.file_path = "dump/" + self.file_name

        # make log folder if one does not exist
        dir = "./dump"
        if not os.path.isdir(dir):
            os.makedirs(dir)

        # If mode is write clear the file
        if(self.mode == "w"):
            if(self.file_name[-4:] == "json"):
                with open(self.file_path, "w") as f:
                    d = {
                        "data": []
                    }
                    json.dump(d, f)
            elif(self.file_name[-3:] == "csv"):
                with open(self.file_path, "w", newline="") as csvfile:
                    writer = csv.DictWriter(csvfile,
                                            fieldnames=self.field_names)
                    writer.writeheader()

    def send_out(self, output_dict: Dict[str, Any],
                 datetime_timestamp: Any) -> None:
        # Execute the send out if time is in range (if that is required)
        if(self.from_hour is None or self.to_hour is None or self.time_in_range(datetime_timestamp)):
            if(self.file_name[-4:] == "json"):
                self.write_JSON(output_dict=output_dict)
            elif(self.file_name[-3:] == "csv"):
                self.write_csv(output_dict=output_dict)
            else:
                print("Output file type not supported.")

    def write_JSON(self, output_dict: Dict[str, Any]) -> None:
        # Read content of file and add output_dict
        with open(self.file_path) as json_file:
            data = json.load(json_file)
            temp = data["data"]
            temp.append(output_dict)
        
        # Write the content back
        with open(self.file_path, "w") as f:
            json.dump(data, f)

    def write_csv(self, output_dict: Dict[str, Any]) -> None:
        with open(self.file_path, 'a', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.field_names)
            writer.writerow(output_dict)
