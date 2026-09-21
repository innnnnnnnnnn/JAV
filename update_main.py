import re

with open('/home/ubuntu/JAV/main.py', 'r') as f:
    content = f.read()

# Update imports to include timedelta if not there
if 'timedelta' not in content:
    content = content.replace('from datetime import datetime, time', 'from datetime import datetime, time, timedelta')

# Update date_str to fetch yesterday
content = content.replace(
    'date_str = datetime.now(TIMEZONE).strftime("%Y/%m/%d")',
    'date_str = (datetime.now(TIMEZONE) - timedelta(days=1)).strftime("%Y/%m/%d")'
)

# Update schedule time to 2:10
content = content.replace(
    'time(hour=22, minute=0, second=0, tzinfo=TIMEZONE)',
    'time(hour=2, minute=10, second=0, tzinfo=TIMEZONE)'
)

with open('/home/ubuntu/JAV/main.py', 'w') as f:
    f.write(content)

print('Updated main.py')
