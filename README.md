# API using flask in Python, connecting to Docker Neo4J container

API description:

-----------------------------------------------------------------------------------------------------------------------------------------------------------------------

-> GETTING WORKERS & DEPARTMENTS <-

- You can "GET" all workers or a specific one by his id (uuidv4). There are also options of sorting workers by passing parameters in the URL. For example, simple "GET" for all workers with "...?sortCategory=asc&sortValue=name" gives you a list of workers in an alphabetical order (given their names). Same goes to departments.

/employees - all worker </br>
/employees/:id - specific worker with given id </br>
/departments - all departments </br>

----------------------------------------------------------------------------------------------------------------------------------------------------------------------

-> ADDING WORKERS <-

- When adding a worker program checks if there already exists a worker with the same first name, last name and a role. If not, it checks if the provided department in request already exists. If it doesn't it creates one, if it does it adds the worker to the provided existing department. Program also checks if provided role is "Manager" - if so, it automatically creates a relationship [:MANAGES] instead of a standard [:WORKS_IN] one.

/employees - add worker ("POST") </br>

-----------------------------------------------------------------------------------------------------------------------------------------------------------------------

-> DELETING WORKERS <-

- When deleting a worker, program checks is he's a department manager. If he is, there are two ways. First - check if anybody except provided worker works at the department, if not - delete it. Second - if there are other workers in the department, the program takes the first from the list and makes him a new manager. If the provided worker is not a manager, he is just deleted, nothing else.

/employees/:id - delete worker with given id ("DELETE") </br>

-----------------------------------------------------------------------------------------------------------------------------------------------------------------------
