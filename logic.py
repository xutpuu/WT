from datetime import datetime, timedelta, date
from dateutil.parser import parse
import aiohttp
import asyncio

def recieveWorkIDsForPeriod(client, dateFrom):
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


def recieveDataForPeriod(client, dateFrom, dateTo):
    workIDs = []
    for i in recieveWorkIDsForPeriod(client, dateFrom)['workItems']:
        workIDs.append(i['id'])

    output = []

    for workID in workIDs:
        entry = []
        entry = dict(id=workID, rev=recieveRevision(client, workID))
        output.append(entry)

    # with open('data.json', 'w') as outfile:
    #     json.dump(output, outfile)

    data = []

    for index in range(len(output)):

        CompletedWork = 0
        for rev in output[index]['rev']:
            if rev['CompletedWork'] > CompletedWork:
                if rev['ChangedDate'] >= dateFrom and rev['ChangedDate'] <= dateTo:
                    delta = timedelta(
                        hours=(rev['CompletedWork']-CompletedWork))
                    entry = dict(id=int(output[index]['id']), StartTime=parse(
                        rev['ChangedDate'], ignoretz=True) - delta, CompletedWork=(rev['CompletedWork']-CompletedWork), ChangedDate=(parse(rev['ChangedDate'], ignoretz=True)), DisplayName=rev['DisplayName'])
                    data.append(entry)
            CompletedWork = rev['CompletedWork']
    
    return data

# async def fetch(workID):
#     async with recieveRevision(workID) as response:
#         return await response

def recieveRevision(client, workID):
    rev = []
    workitem = client.get_workitem(workID)
    re = workitem.data['rev']
    for revision in range(0, re, 200):
        call = client.get_json('https://imagineer.visualstudio.com/_apis/wit/workitems/' +
                               str(workID)+'/revisions?$skip='+str(revision)+'&api-version=5.1')
        CompletedWork = 0
        for i in call['value']:
            if 'Microsoft.VSTS.Scheduling.CompletedWork' in i['fields']:
                l = dict(DisplayName=i.get('fields')['System.ChangedBy']['displayName'], CompletedWork=i.get('fields')[
                    'Microsoft.VSTS.Scheduling.CompletedWork'], ChangedDate=i.get('fields')['System.ChangedDate'], Revision=i.get("rev"))
                CompletedWork = i.get('fields')[
                    'Microsoft.VSTS.Scheduling.CompletedWork']
                rev.append(l)
            else:
                l = dict(DisplayName=i.get('fields')['System.ChangedBy']['displayName'], CompletedWork=CompletedWork, ChangedDate=i.get(
                    'fields')['System.ChangedDate'], Revision=i.get("rev"))
                rev.append(l)
    return rev