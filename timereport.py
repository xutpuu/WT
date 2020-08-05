import json
import openpyxl
import pandas as pd
from tfs import TFSAPI
from datetime import datetime, timedelta
from dateutil.parser import parse

dateFrom = "2020-08-03"
dateTo = "2020-08-09"

with open('config.json') as config_file:
    configs = json.load(config_file)
    config_token = configs['token']
client = TFSAPI(configs['server'],
                project=configs['project'], pat=config_token)


def convertTime(dateTime):
    return parser.parse(dateTime).strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def recieveWorkIDsforPeriod(dateFrom, dateTo):
    query = """ SELECT
                    [System.Id],
                    [System.WorkItemType],
                    [System.Title],
                    [System.ChangedDate]
                FROM workitems
                WHERE
                    [System.ChangedDate] >= """+"'"+dateFrom+"'"+""" AND
                    ( [Work Item Type]='Task' OR 
                    [Work Item Type]='Code Review Response' OR 
                    [Work Item Type]='Test Case' )
                ORDER BY [System.ChangedDate]"""
    return client.run_wiql(query)


workIDs = []
wiql = recieveWorkIDsforPeriod(dateFrom, dateTo)
for i in wiql['workItems']:
    workIDs.append(i['id'])

f = open('log.json', 'w')
output = []

for workID in workIDs:
    entry = []
    rev = []
    workitem = client.get_workitem(workID)
    re = workitem.data['rev']
    for revision in range(0, re, 200):
        call = client.get_json('https://imagineer.visualstudio.com/_apis/wit/workitems/' +
                               str(workID)+'/revisions?$skip='+str(revision)+'&api-version=5.1')
        CompletedWork = 0
        for i in call['value']:
            if 'Microsoft.VSTS.Scheduling.CompletedWork' in i['fields']:
               # if convertTime(i.get('fields')['System.ChangedDate']) >= convertTime(dateFrom) and convertTime(i.get('fields')['System.ChangedDate']) < convertTime(dateTo):
                l = dict(DisplayName=i.get('fields')['System.ChangedBy']['displayName'], CompletedWork=i.get('fields')[
                         'Microsoft.VSTS.Scheduling.CompletedWork'], ChangedDate=i.get('fields')['System.ChangedDate'], Revision=i.get("rev"))
                CompletedWork = i.get('fields')[
                    'Microsoft.VSTS.Scheduling.CompletedWork']
                rev.append(l)
            else:
                l = dict(DisplayName=i.get('fields')['System.ChangedBy']['displayName'], CompletedWork=CompletedWork, ChangedDate=i.get(
                    'fields')['System.ChangedDate'], Revision=i.get("rev"))
                rev.append(l)
    entry = dict(id = workID, rev = rev)
    output.append(entry)

json.dump(output, f)
f.close


with open('log.json') as json_file:
    data = json.load(json_file)

data_fixed = []

for index in range(len(data)):
    CompletedWork = 0
    for rev in data[index]['rev']:
        if rev['CompletedWork'] > CompletedWork:
            if rev['ChangedDate'] >= dateFrom and rev['ChangedDate'] <= dateTo:
                delta = timedelta(hours=(rev['CompletedWork']-CompletedWork))
                entry = dict(id=int(data[index]['id']), StartTime=parse(
                    rev['ChangedDate'], ignoretz=True) - delta, CompletedWork=(rev['CompletedWork']-CompletedWork), ChangedDate=(parse(rev['ChangedDate'], ignoretz=True)), DisplayName=rev['DisplayName'])
                data_fixed.append(entry)
        CompletedWork = rev['CompletedWork']

# pd.Series(data_fixed).to_frame('index')
df = pd.DataFrame(data_fixed, columns=[
                  "id", "StartTime", "CompletedWork", "ChangedDate", "DisplayName"])

# mask  = df['DisplayName'].str.contains('Yuliia')
# df = df.loc[mask]

df['Date'] = pd.to_datetime(df['ChangedDate']).dt.date

#df1 = df.groupby(["id","Date","DisplayName","StartTime"]).sum().sort_values(['DisplayName', 'StartTime'])
# df1.to_excel("output.xlsx")
df1 = df.sort_values(['DisplayName', 'StartTime'])
df1.to_excel("output.xlsx")
print(df1)
