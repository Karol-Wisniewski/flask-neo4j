CREATE (e:Employee {firstName:"Jan", lastName: "Kowalski", role:"Manager"})-[:MANAGES]->(d:Department {name: "IT"})
CREATE (e:Employee {firstName:"Grzegorz", lastName: "Migdalski", role:"Janitor"})-[:WORKS_IN]->(d:Department {name: "IT"})
CREATE (e:Employee {firstName:"Szymon", lastName: "Maciejewicz", role:"Accountant"})-[:WORKS_IN]->(d:Department {name: "IT"})
CREATE (e:Employee {firstName:"Anna", lastName: "Wiśniewska", role:"Manager"})-[:MANAGES]->(d:Department {name: "FINANCES"})
CREATE (e:Employee {firstName:"Maciek", lastName: "Kowalczyk", role:"Intern"})-[:WORKS_IN]->(d:Department {name: "FINANCES"})