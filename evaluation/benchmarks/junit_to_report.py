"""Normalize Surefire/JUnit evidence; never infer passes from empty reports."""
import hashlib, json, pathlib, sys, xml.etree.ElementTree as ET

def convert(paths):
    specs, sources = [], []
    for name in paths:
        raw = pathlib.Path(name).read_bytes()
        if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper(): raise ValueError('DTD/entities unsupported')
        root = ET.fromstring(raw)
        if root.tag not in ('testsuite','testsuites'): raise ValueError('Expected JUnit suite')
        sources.append({'file':pathlib.Path(name).name,'sha256':hashlib.sha256(raw).hexdigest()})
        for case in root.iter('testcase'):
            if not case.get('classname') or not case.get('name'): raise ValueError('Missing identity')
            status = 'failed' if case.find('failure') is not None or case.find('error') is not None else 'skipped' if case.find('skipped') is not None else 'passed'
            specs.append({'title':case.get('classname')+'#'+case.get('name'),'tests':[{'expectedStatus':'passed','results':[{'status':status}]}]})
    if not specs: raise ValueError('No test cases')
    return {'suites':[{'specs':specs}],'sourceReports':sources}
if __name__ == '__main__':
    if len(sys.argv)<3: raise SystemExit('Usage: junit_to_report.py OUTPUT.json INPUT.xml [INPUT.xml...]')
    report=convert(sys.argv[2:]);out=pathlib.Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
