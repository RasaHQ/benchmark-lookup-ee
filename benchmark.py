import sys
import time
import argparse
import matplotlib.pyplot as plt

from typing import Text, List, Dict
from rasa.shared.utils.io import read_file
from rasa.shared.nlu.constants import TEXT, ENTITIES
from rasa.nlu.extractors.extractor import EntityExtractor
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.shared.nlu.training_data.formats.rasa_yaml import RasaYAMLReader
from rasa.nlu.extractors.regex_entity_extractor import RegexEntityExtractor
from rasa_nlu_examples.extractors.flashtext_entity_extractor import FlashTextEntityExtractor


def messages_from_file(filename: Text) -> TrainingData:
    data = TrainingData()
    with open(filename, "r") as f:
        for line in f:
            data.training_examples.append(Message(data={TEXT: line}))
    return data


def time_process(extractor: EntityExtractor, test_data: TrainingData) -> float:
    total_elapsed = 0.0
    for message in test_data.training_examples:
        start = time.time()
        extractor.process(message)
        end = time.time()
        total_elapsed += (end - start)
        message.set(ENTITIES, [])  # wipe the message
    return total_elapsed


def generate_steps(start: int, end: int) -> List[int]:
    current = start
    steps = []
    while current < end:
        steps.append(current)
        if current < 100:
            stepsize = 10
        elif current < 1000:
            stepsize = 100
        else:
            stepsize = 1000
        current += stepsize
    steps.append(end + 1)
    return steps


def plot_results(results: Dict[Text, List[float]], num_lookup_range: List[float], num_messages: int) -> None:
    fig = plt.figure()
    ax = fig.add_subplot()
    for name, times in results.items():
        ax.scatter(num_lookup_range, times, label=name)
    plt.legend(loc="upper left")
    ax.set_title(f'Benchmark Lookup Entity Extractors\n{(" vs ".join(results.keys()))}')
    ax.set_xlabel('number of lookup patterns')
    ax.set_ylabel(f'time taken (s) to process {num_messages} messages')
    plt.show()


def main():
    parser = argparse.ArgumentParser(description='Benchmark lookup entity extractors.')
    parser.add_argument('--test', default='data/tennis_test.txt',
                        help='test data, one message per line. default: \'data/tennis_test.txt\'')
    parser.add_argument('--nlu', default='data/nlu.yml',
                        help='nlu file with lookup and training examples. default: \'data/nlu.yml\'')
    parser.add_argument('--start', default=10, help='start value for range of number of lookups.')
    parser.add_argument('--lookup', help='entity type, default: first lookup found', required=False)
    args = parser.parse_args()
    test_data = messages_from_file(args.test)

    training_data = RasaYAMLReader().reads(read_file(args.nlu))
    if args.lookup:
        for lookup in training_data.lookup_tables:
            if lookup['name'] == args.lookup:
                training_data.lookup_tables = [lookup]
                break
    else:
        training_data.lookup_tables = [training_data.lookup_tables[0]]

    if len(training_data.training_examples) < 2:
        sys.stderr.write(f"You must have at least two nlu examples per entity type.")
        exit(1)

    extractors = {'FlashTextEntityExtractor': FlashTextEntityExtractor(),
                  'RegexEntityExtractor': RegexEntityExtractor()}
    num_lookup_range = generate_steps(args.start, len(training_data.lookup_tables[0]['elements']))
    all_lookups = training_data.lookup_tables[0]['elements']

    results = {}
    for extractor_name, extractor in extractors.items():
        times = []
        for num_lookup in num_lookup_range:
            training_data.lookup_tables[0]['elements'] = all_lookups[:num_lookup]
            extractor.train(training_data)
            times.append(time_process(extractor, test_data))
        results[extractor_name] = times
    plot_results(results, num_lookup_range, len(test_data.training_examples))


if __name__ == "__main__":
    main()