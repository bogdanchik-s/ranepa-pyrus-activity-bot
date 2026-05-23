from typing import Literal


MessageSystemAttributeName = Literal[
    'All',
    'ApproximateFirstReceiveTimestamp',
    'ApproximateReceiveCount',
    'AWSTraceHeader',
    'DeadLetterQueueSourceArn',
    'MessageDeduplicationId',
    'MessageGroupId',
    'SenderId',
    'SentTimestamp',
    'SequenceNumber',
]
