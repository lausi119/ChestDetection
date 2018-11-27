import os
import json

# define keypoints:
RIGHT_SHOULDER_X = 2*3
RIGHT_SHOULDER_Y = 2*3+1
LEFT_SHOULDER_X = 5*3
LEFT_SHOULDER_Y = 5*3+1
RIGHT_HIP_X = 9*3
RIGHT_HIP_Y = 9*3+1
LEFT_HIP_X = 12*3
LEFT_HIP_Y = 12*3+1

class Person:
    def __init__(self, right_shoulder_x, right_shoulder_y, left_shoulder_x, left_shoulder_y, right_hip_x, right_hip_y, left_hip_x, left_hip_y):
        self.right_shoulder_x = right_shoulder_x
        self.right_shoulder_y = right_shoulder_y
        self.left_shoulder_x = left_shoulder_x
        self.left_shoulder_y = left_shoulder_y
        self.right_hip_x = right_hip_x
        self.right_hip_y = right_hip_y
        self.left_hip_x = left_hip_x
        self.left_hip_y = left_hip_y


def extract_frame_chests(keypoint_json):
    person_array = []
    for person in keypoint_json['people']:
        person_array.append( Person(person['pose_keypoints_2d'][RIGHT_SHOULDER_X],
                                    person['pose_keypoints_2d'][RIGHT_SHOULDER_Y],
                                    person['pose_keypoints_2d'][LEFT_SHOULDER_X],
                                    person['pose_keypoints_2d'][LEFT_SHOULDER_Y],
                                    person['pose_keypoints_2d'][RIGHT_HIP_X],
                                    person['pose_keypoints_2d'][RIGHT_HIP_Y],
                                    person['pose_keypoints_2d'][LEFT_HIP_X],
                                    person['pose_keypoints_2d'][LEFT_HIP_Y])
                            )
    return person_array

#define
SAME_PERSON_THRESHOLD_FACTOR = 0.1

def person_matches(person1, person2):
    
#    determined by shoulder width + hip to shoulder height
    size_person1 = (person1.left_shoulder_x - person1.right_shoulder_x + person1.right_hip_y - person1.right_shoulder_y)
    size_person1_factor = size_person1 * SAME_PERSON_THRESHOLD_FACTOR
    x1 = abs(person1.right_shoulder_x - person2.right_shoulder_x)
    x2 = abs(person1.left_shoulder_x - person2.left_shoulder_x)
    x3 = abs(person1.right_hip_x - person2.right_hip_x)
    x4 = abs(person1.left_hip_x - person2.left_hip_x)
    y1 = abs(person1.right_shoulder_y - person2.right_shoulder_y)
    y2 = abs(person1.left_shoulder_y - person2.left_shoulder_y)
    y3 = abs(person1.right_hip_y - person2.right_hip_y)
    y4 = abs(person1.left_hip_y - person2.left_hip_y)
    
    if x1 < size_person1_factor and x2 < size_person1_factor and x3 < size_person1_factor and x4 < size_person1_factor and y1 < size_person1_factor and y2 < size_person1_factor and y3 < size_person1_factor and y4 < size_person1_factor:
        return True
    else:
        return False


def reorganize_to_by_person(chests_by_frame):
    by_person = []
    max_people = 0
    frame = chests_by_frame[0]
    for person in frame:
        person_list = []
        person_list.append(person)
        by_person.append(person_list)
        max_people = max_people + 1
    
    for x in range(len(chests_by_frame) - 1):
        frame = chests_by_frame[x+1]
        for person_in_frame in frame:
            person_assigned = 0
            for person in by_person:
                if person_matches(person_in_frame, person[-1]):
                    person.append(person_in_frame)
                    person_assigned = 1
                    break
            if person_assigned == 0:
                person_list = []
                person_list.append(person_in_frame)
                by_person.append(person_list)
                max_people = max_people + 1

    return by_person

# define
SEQUENCE_THRESHOLD = 10
CHEST_BUFFER = 10

class Sequence:
    def __init__(self, start, end, x1, y1, x2, y2, x3, y3, x4, y4):
        self.start = start
        self.end = end
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x3 = x3
        self.y3 = y3
        self.x4 = x4
        self.y4 = y4


def set_sequence_coordinates(start, end, person):
    x1 = 0
    y1 = 0
    x2 = 0
    y2 = 0
    x3 = 0
    y3 = 0
    x4 = 0
    y4 = 0
    length = end - start + 1
    for index in range(length):
        x1 = x1 + person[index].right_shoulder_x
        y1 = y1 + person[index].right_shoulder_y
        x2 = x2 + person[index].left_shoulder_x
        y2 = y2 + person[index].left_shoulder_x
        x3 = x3 + person[index].right_hip_x
        y3 = y3 + person[index].right_hip_y
        x4 = x4 + person[index].left_hip_x
        y4 = y4 + person[index].left_hip_y

#maybe do not apply to all ? maybe apply different values
    x1 = x1/length - CHEST_BUFFER
    y1 = y1/length - CHEST_BUFFER
    x2 = x2/length + CHEST_BUFFER
    y2 = y2/length - CHEST_BUFFER
    x3 = x3/length - CHEST_BUFFER
    y3 = y3/length + CHEST_BUFFER
    x4 = x4/length + CHEST_BUFFER
    y4 = y4/length + CHEST_BUFFER
    return Sequence(start, end, x1, y1, x2, y2, x3, y3, x4, y4)


def extract_sequences(people):
    start = 0
    end = 0
    people_sequences = []

    for person in people:
        sequences = []
        start = 0
        end = 0
        for index in range(len(person) - 1):
            if abs(person[index].right_shoulder_x - person[index + 1].right_shoulder_x) > SEQUENCE_THRESHOLD and abs(person[index].left_shoulder_x - person[index + 1].left_shoulder_x) > SEQUENCE_THRESHOLD and abs(person[index].right_hip_x - person[index + 1].right_hip_x) > SEQUENCE_THRESHOLD and abs(person[index].left_hip_x - person[index + 1].left_hip_x) > SEQUENCE_THRESHOLD:

                end = index + 1
            else:
                sequence = set_sequence_coordinates(start, end, person)
                sequences.append(sequence)
                start = index
                end = index
        sequences.append(set_sequence_coordinates(start, end, person))
        people_sequences.append(sequences)

    return people





PATH = '/Users/laurenzschmielau/Desktop/CPEN491/openpose/examples/example_results_json/'
#    TODO

def test():
#    print(~/Desktop/CPEN491/openpose/examples/example_results_json/video_000000000000_keypoints.json)
#    print(os.getcwd())
#    print(os.path.dirname(__file__))

    file = open('/Users/laurenzschmielau/Desktop/CPEN491/openpose/examples/example_results_json/video_000000000000_keypoints.json', 'r')
    keypoint_file = file.read()
    keypoint_json = json.loads(keypoint_file)
    
    chests_by_frame = []
    
    filelist = os.listdir(PATH)
    for file in filelist:
        keypoint_json = json.loads(open(PATH + file, 'r').read())
        chests_by_frame.append(extract_frame_chests(keypoint_json))

    chests_by_person = reorganize_to_by_person(chests_by_frame)
    sequences_by_person = extract_sequences(chests_by_person)

    print(sequences_by_person)

test()
