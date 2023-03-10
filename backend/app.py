from flask import Flask, jsonify, request
from neo4j import GraphDatabase
import requests
import uuid

app = Flask(__name__)

uri = "neo4j+s://45730ae3.databases.neo4j.io"

user = "neo4j"

password = "PmkhSEZ_5Lp59gPtMbHSYRA3LBjGObf4-RjSHxAOALk"

driver = GraphDatabase.driver(uri, auth=(user, password), database="neo4j")

@app.route('/', methods=['GET'])
def default_get():
    return "Flask API is live"

#GET WORKERS WITH FILTERS
def get_workers(tx, sortValue='', sortCategory='', filterValue='', filterCategory=''):
    query = "MATCH (e:Employee)-[r]-(d:Department) RETURN e, d"
    if (sortCategory == 'asc'):
        if (sortValue == 'firstName'):
            query = "MATCH (e:Employee) RETURN e, d ORDER BY e.firstName"
        elif (sortValue == 'lastName'):
            query = "MATCH (e:Employee) RETURN e, d ORDER BY e.lastName"
        elif (sortValue == 'role'):
            query = "MATCH (e:Employee) RETURN e, d ORDER BY e.role"
    if (sortCategory == 'desc'):
        if (sortValue == 'firstName'):
            query = "MATCH (e:Employee) RETURN e, d ORDER BY e.firstName DESC"
        elif (sortValue == 'lastName'):
            query = "MATCH (e:Employee) RETURN e, d ORDER BY e.lastName DESC"
        elif (sortValue == 'role'):
            query = "MATCH (e:Employee) RETURN e, d ORDER BY e.role DESC"    
    if (filterCategory == 'firstName'):
        query = f"MATCH (e:Employee) WHERE e.firstName CONTAINS '{filterValue}' RETURN e, d"          
    if (filterCategory == 'lastName'):
        query = f"MATCH (e:Employee) WHERE e.surname CONTAINS '{filterValue}' RETURN e, d"   
    if (filterCategory == 'role'):
        query = f"MATCH (e:Employee) WHERE e.role CONTAINS '{filterValue}' RETURN e, d"                 
    results = tx.run(query).data()
    workers = [{'id': result['e']['id'], 'firstName': result['e']['firstName'], 'lastName': result['e']['lastName'], 'role': result['e']['role'], 'department': result['d']['name']} for result in results]
    return workers

@app.route('/employees', methods=['GET'])
def get_workers_route():
    args = request.args
    sortValue = args.get("sortValue")
    filterCategory = args.get("filterCategory")
    sortCategory = args.get("sortCategory")
    filterValue = args.get("filterValue")
    with driver.session() as session:
        workers = session.read_transaction(get_workers, sortValue, sortCategory, filterValue, filterCategory)
    response = {'workers': workers}
    return jsonify(response)


#GET WORKER BY ID
def get_worker_by_id(tx, id):
    getWorker = f"MATCH (e:Employee)-[r]-(d:Department) WHERE e.id = '{id}' RETURN e, d"
    result = tx.run(getWorker).data()
    if not result:
        return {'message': 'Employee not found', 'status': 404}
    else:
        return {'id': result[0]['e']['id'], 'firstName': result[0]['e']['firstName'], 'lastName': result[0]['e']['lastName'], 'role': result[0]['e']['role'], 'department': result[0]['d']['name']}

@app.route('/employees/<id>', methods=['GET'])
def get_worker_by_id_route(id):
    workerId = id
    with driver.session() as session:
        res = session.read_transaction(get_worker_by_id, workerId)
    return jsonify(res)


#GET WORKER SUBORDINATES
def get_worker_subordinates(tx, id):
    getWorker = f"MATCH (e:Employee) WHERE e.id = '{id}' RETURN e"
    checkIfManager = f"MATCH (e:Employee)-[r:MANAGES]-(d:Department) WHERE e.id = '{id}' RETURN e, d"
    workerExists = tx.run(getWorker).data()
    isManager = tx.run(checkIfManager).data()
    if not workerExists:
        return {'message': 'Employee not found', 'status': 404}
    else:
        if not isManager:
            return {'message': 'Employee is not a manager', 'status': 400}
        else:
            manager = requests.get(f'http://127.0.0.1:5000/employees/{id}').json()
            managerDepartment = manager["department"]
            getSubordinates=f"MATCH (e:Employee)-[r:WORKS_IN]-(d:Department) WHERE d.name = '{managerDepartment}' RETURN e, d"
            subordinates = tx.run(getSubordinates, managerDepartment=managerDepartment).data()
            result = [{'id': subordinate['e']['id'], 'firstName': subordinate['e']['firstName'], 'lastName': subordinate['e']['lastName'], 'role': subordinate['e']['role'], 'department': subordinate['d']['name']} for subordinate in subordinates]
            return {'subordinates': result}

@app.route('/employees/<id>/subordinates', methods=['GET'])
def get_worker_subordinates_route(id):
    workerId = id
    with driver.session() as session:
        res = session.read_transaction(get_worker_subordinates, workerId)
    return jsonify(res)


#ADD WORKER
def add_worker(tx, firstName, lastName, role, department):
    checkIfUnique = f"MATCH (e:Employee) WHERE e.firstName='{firstName}' AND e.lastName='{lastName}' AND e.role='{role}' RETURN e"
    result = tx.run(checkIfUnique, firstName=firstName).data()
    if not result: 
        queryWithoutExistingDepartmentRegular = f"CREATE (e:Employee {{id: '{str(uuid.uuid4())}', firstName:'{firstName}', lastName:'{lastName}', role:'{role}'}})-[:WORKS_IN]->(d:Department {{name: '{department}'}})"
        queryWithExistingDepartmentRegular = f"MATCH (d:Department {{name: '{department}'}}) CREATE (e:Employee {{id: '{str(uuid.uuid4())}', firstName:'{firstName}', lastName:'{lastName}', role:'{role}'}})-[r:WORKS_IN]->(d)"
        queryWithoutExistingDepartmentManager = f"CREATE (e:Employee {{id: '{str(uuid.uuid4())}', firstName:'{firstName}', lastName:'{lastName}', role:'{role}'}})-[:MANAGES]->(d:Department {{name: '{department}'}})"
        queryWithExistingDepartmentManager = f"MATCH (d:Department {{name: '{department}'}}) CREATE (e:Employee {{id: '{str(uuid.uuid4())}', firstName:'{firstName}', lastName:'{lastName}', role:'{role}'}})-[r:MANAGES]->(d)"
        checkIfDepartmentExists = f"MATCH (d:Department) WHERE d.name = '{department}' RETURN d"
        existingDepartment = tx.run(checkIfDepartmentExists, department=department).data()
        if not existingDepartment:
            if (role == "Manager" or role == "manager"):
                tx.run(queryWithoutExistingDepartmentManager, firstName=firstName, lastName=lastName, role=role, department=department)
                return {'message': 'Manager added and department created successfully', 'status': 200}
            else:
                tx.run(queryWithoutExistingDepartmentRegular, firstName=firstName, lastName=lastName, role=role, department=department)
                return {'message': 'Employee added and department created successfully', 'status': 200}
        else:
            if (role == "Manager" or role == "manager"):
                tx.run(queryWithExistingDepartmentManager, firstName=firstName, lastName=lastName, role=role, department=department)
                return {'message': 'Manager added successfully', 'status': 200}
            else:
                tx.run(queryWithExistingDepartmentRegular, firstName=firstName, lastName=lastName, role=role, department=department)
                return {'message': 'Employee added successfully', 'status': 200}
    else:
        return {'message': 'Employee already exists', 'status': 409}

@app.route('/employees', methods=['POST'])
def add_worker_route():
    data = request.json
    firstName = data['firstName']
    lastName = data['lastName']
    role = data['role']
    department = data['department']
    print("")
    print("Adding worker:")
    print(firstName, lastName, ": ", role, " in ", department)
    print("")
    if (firstName == '' or lastName == '' or role == '' or department == ''):
        return 'Provide all neccesary data - first name, last name, role and department'

    with driver.session() as session:
        res = session.write_transaction(add_worker, firstName, lastName, role, department)

    return jsonify(res)


#UPDATE WORKER
def update_worker(tx, workerId, newFirstName, newLastName, newRole, newDepartment):
    worker = requests.get(f'http://127.0.0.1:5000/employees/{workerId}').json()
    if not worker:
        return None
    else:
        query = f"MATCH (e:Employee {{id: '{workerId}'}})-[r]-(d:Department) SET e.firstName='{newFirstName}', e.lastName='{newLastName}', e.role='{newRole}' DELETE r"
        tx.run(query, newFirstName=newFirstName, newLastName=newLastName, newRole=newRole)
        
        queryWithoutExistingDepartmentRegular = f"MATCH (e:Employee {{id: '{workerId}'}}) CREATE (e)-[r:WORKS_IN]->(d:Department {{name: '{newDepartment}'}})"
        queryWithExistingDepartmentRegular = f"MATCH (d:Department {{name: '{newDepartment}'}}), (e:Employee {{id: '{workerId}'}}) CREATE (e)-[r:WORKS_IN]->(d)"
        queryWithoutExistingDepartmentManager = f"MATCH (e:Employee {{id: '{workerId}'}}) CREATE (e)-[r:MANAGES]->(d:Department {{name: '{newDepartment}'}})"
        queryWithExistingDepartmentManager = f"MATCH (d:Department {{name: '{newDepartment}'}}), (e:Employee {{id: '{workerId}'}}) CREATE (e)-[r:MANAGES]->(d)"
        checkIfWorkerIsManager = f"MATCH (e:Employee) WHERE e.id = '{workerId}' AND toLower(e.role) = 'manager' RETURN e"
        checkIfDepartmentExists = f"MATCH (d:Department) WHERE d.name = '{newDepartment}' RETURN d"
        checkDepartmentExistence = tx.run(checkIfDepartmentExists, newDepartment=newDepartment).data()
        checkWorkerManagement = tx.run(checkIfWorkerIsManager, workerId=workerId).data()
        
        if not checkDepartmentExistence:
            if checkWorkerManagement:
                tx.run(queryWithoutExistingDepartmentManager, firstName=newFirstName, lastName=newLastName, role=newRole, newDepartment=newDepartment)
                return {'message': 'Employee updated and moved to newly created department as a Manager', 'status': 200}
            else:
                tx.run(queryWithoutExistingDepartmentRegular, firstName=newFirstName, lastName=newLastName, role=newRole, newDepartment=newDepartment)
                return {'message': 'Employee updated and moved to newly created department', 'status': 200}
        else:
            if checkWorkerManagement:
                tx.run(queryWithExistingDepartmentManager, firstName=newFirstName, lastName=newLastName, role=newRole, newDepartment=newDepartment)
                return {'message': 'Employee updated', 'status': 200}
            else:
                tx.run(queryWithExistingDepartmentRegular, firstName=newFirstName, lastName=newLastName, role=newRole, newDepartment=newDepartment)
                return {'message': 'Employee updated', 'status': 200}

@app.route('/employees/<id>', methods=['PUT'])
def update_worker_route(id):
    workerId = id
    data = request.json
    newFirstName = data['firstName']
    newLastName = data['lastName']
    newRole = data['role']
    newDepartment = data['department']

    with driver.session() as session:
        res = session.write_transaction(update_worker, workerId, newFirstName, newLastName, newRole, newDepartment)
        
    print("")
    print(f"Updating worker with id '{workerId}' to following data:")
    print(newFirstName, newLastName, ": ", newRole, " in ", newDepartment)
    print("")
    
    if (newFirstName == '' or newLastName == '' or newRole == '' or newDepartment == ''):
        return jsonify('Provide all neccesary data to update - first name, last name, role and department')

    if not res:
        response = {'message': 'Employee not found', 'status': 404}
        return jsonify(response)
    else:
        response = {'status': 200, 'message': 'Employee updated'}
        return jsonify(res)


def delete_worker_by_id(tx, workerId):
    worker = requests.get(f'http://127.0.0.1:5000/employees/{workerId}').json() 
    if not worker:
        return {'message': 'Worker not found', 'status': 404}
    else:
        workerDepartment = worker["department"]
        if (worker["role"] == "Manager"):
            deleteWorker = f"MATCH (e:Employee) WHERE e.id = '{workerId}' DETACH DELETE e"
            tx.run(deleteWorker, workerId=workerId)
            getOtherWorkersInSameDepartment = f"MATCH (e:Employee)-[r]-(d:Department {{name:'{workerDepartment}'}}) RETURN e"
            otherWorkers = tx.run(getOtherWorkersInSameDepartment, workerDepartment=workerDepartment).data()
            if (len(otherWorkers) == 0):
                deleteDepartment = f"MATCH (d:Department) WHERE d.name='{workerDepartment}' DELETE d"
                tx.run(deleteDepartment, workerDepartment=workerDepartment)
                return {'message': 'Worker fired, department had to be closed', 'status': 200}
            else:
                newManagerId = otherWorkers[0]["e"]["id"]
                createNewManager = f"MATCH (e:Employee)-[r]-(d:Department) WHERE e.id = '{newManagerId}' SET e.role='Manager' DETACH DELETE r CREATE (e)-[:MANAGES]->(d) RETURN e"
                newlyCreatedManager = tx.run(createNewManager, newManagerId = newManagerId).data()
                return {'message': f"Worker fired, department has a new manager: {newlyCreatedManager[0]['e']['firstName']} {newlyCreatedManager[0]['e']['lastName']}", 'status': 200}
        else:
            deleteWorker = f"MATCH (e:Employee) WHERE e.id = '{workerId}' DETACH DELETE e"
            tx.run(deleteWorker, workerId=workerId)
            return {'message': 'Worker fired, no changes for the department', 'status': 200}


@app.route('/employees/<id>', methods=['DELETE'])
def delete_worker_by_id_route(id):

    workerId = id
    
    with driver.session() as session:
        res = session.write_transaction(delete_worker_by_id, workerId)

    return jsonify(res)


#GET DEPARTMENTS WITH FILTERS
def get_departments(tx, sortValue='', sortCategory='', filterValue='', filterCategory=''):
    query = "MATCH (d:Department) RETURN d"
    if (sortCategory == 'asc'):
        if (sortValue == 'name'):
            query = "MATCH (d:Department) RETURN d ORDER BY d.name"
        if (sortValue == 'numberOfEmployees'):
            query = "MATCH (e:Employee)-[r]-(d:Department) WITH d, count(*) AS count RETURN d ORDER BY count"    
    if (sortCategory == 'desc'):        
        if (sortValue == 'name'):
            query = "MATCH (d:Department) RETURN d ORDER BY d.name DESC"
        if (sortValue == 'numberOfEmployees'):
            query = "MATCH (e:Employee)-[r]-(d:Department) WITH d, count(*) AS count RETURN d ORDER BY count DESC"    
    if (filterCategory == 'name'):
        query = f"MATCH (d:Department) WHERE toLower(d.name) CONTAINS toLower('{filterValue}') RETURN d"
    results = tx.run(query).data()
    departments = [{'name': result['d']['name']} for result in results]
    return departments


@app.route('/departments', methods=['GET'])
def get_departments_route():
    args = request.args
    sortValue = args.get("sortValue")
    filterCategory = args.get("filterCategory")
    sortCategory = args.get("sortCategory")
    filterValue = args.get("filterValue")
    with driver.session() as session:
        departments = session.read_transaction(get_departments, sortValue, sortCategory, filterValue, filterCategory)
    response = {'departments': departments}
    return jsonify(response)


#GET DEPARTMENT
def get_department_by_name(tx, departmentName):
    query = f"MATCH (e:Employee)-[r]-(d:Department {{name: '{departmentName}'}}) RETURN e, d"
    findManager=f"MATCH (e:Employee)-[r:MANAGES]-(d:Department {{name: '{departmentName}'}}) RETURN e"
    results = tx.run(query).data()
    manager = tx.run(findManager).data()
    if not results:
        return {'message': 'No department found', 'status': 404}
    else:
        departmentInfo = {'name': results[0]['d']['name'], 'numberOfWorkers': len(results), 'workers': [result['e'] for result in results], 'manager': f"{manager[0]['e']['firstName']} {manager[0]['e']['lastName']}"}
        return departmentInfo


@app.route('/departments/<string:name>', methods=['GET'])
def get_department_by_name_route(name):

    departmentName = name

    with driver.session() as session:
        res = session.read_transaction(get_department_by_name, departmentName)
    return jsonify(res)


#GET DEPARTMENT EMPLOYEES
def get_department_employees(tx, departmentName):
    query = f"MATCH (e:Employee)-[r:WORKS_IN]-(d:Department {{name: '{departmentName}'}}) RETURN e, d"
    results = tx.run(query).data()
    if not results:
        return {'message': 'No department found or there are no workers in it', 'status': 404}
    else:
        departmentInfo = {'workers': [result['e'] for result in results]}
        return departmentInfo


@app.route('/departments/<string:name>/employees', methods=['GET'])
def get_department_employees_route(name):

    departmentName = name

    with driver.session() as session:
        res = session.read_transaction(get_department_employees, departmentName)
    return jsonify(res)