#!/usr/bin/env python

import sys
import os
import time
import boto3 as b3
from botocore.exceptions import ClientError
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

client = b3.client('rekognition')
collection = None

class MotionEventHandler(PatternMatchingEventHandler):
    patterns = ["*.jpg"]

    def on_created(self, event):
        print(event.src_path, event.event_type)
        event_file = open(event.src_path, 'rb')
        image = event_file.read()

        response_check = client.detect_faces(Image={'Bytes': image})
        if not response_check['FaceDetails']:
            print 'No face detected, deleting file...'
            event_file.flush()
            event_file.close()
            try:
                os.remove(event.src_path)
            except OSError:
                print 'Cannot delete file, check permissions'
        else:
            print 'Face detected, identifying...'
            try:
                resp = client.search_faces_by_image(
                    CollectionId=collection,
                    Image={'Bytes': image},
                    MaxFaces=1,
                    FaceMatchThreshold=85)
                with open('event.log', 'a+') as check:
                    if not resp['FaceMatches']:
                        check.write('%s | Unknown Person | %s\n' %
                                    (time.strftime('%Y-%m-%d %H:%M:%S'), event.src_path))
                    else:
                        check.write('%s | %s | %s\n' % (
                            time.strftime('%Y-%m-%d %H:%M:%S'),
                            resp['FaceMatches'][0]['Face']['ExternalImageId'],
                            event.src_path))
            except ClientError as exception:
                print 'Error: %s' % exception.response['Error']['Code']
            event_file.flush()
            event_file.close()

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    collection = sys.argv[2] if len(sys.argv) > 2 else 'camerapi'
    print collection
    observer = Observer()
    event_handler = MotionEventHandler()
    observer.schedule(event_handler, path)
    print 'Starting observer on %s' % path
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == '__main__':
    main()
