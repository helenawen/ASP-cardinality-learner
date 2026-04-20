# DBpedia Benchmark Queries
## Apache Jena Fuseki – Constructed Knowledge Graph Test Sets

This repository contains a collection of SPARQL CONSTRUCT and SELECT queries used to generate positive (P) and negative (N) training and evaluation datasets from DBpedia.

The goal is to create graph-structured learning problems where entities satisfy (P) or violate (N) majority-based relational conditions.

---

### Dataset Sizes
Each test case is generated in multiple sizes by changing the LIMIT parameter within the inner subqueries.

*Companies & Subsidiaries.*

| Size | Per class (P / N) | Total |
| :--- | :--- | :--- |
| **XS** | 25 | 50 |
| **S** | 100 | 200 |
| **M** | 200 | 400 |
| **L** | 500 | 1000 |
| **XL** | 800 | 1600 |

*Cities, Universities & Museums.*

| Size | Per class (P / N) | Total |
| :--- |:------------------|:------|
| **S** | 25                | 50    |
| **M** | 50                | 100   |
| **L** | 100               | 200   |
---

## Part I — Companies & Subsidiaries
**Dataset family:** dbpedia-subsidiaries-*
**Logic:** Classifies companies based on whether they have more subsidiaries than products (P) or more products than subsidiaries (N).

### Positive Class (P)
*Companies with more subsidiaries than products.*

#### Ontology Graph (CONSTRUCT)
```
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo:  <http://dbpedia.org/ontology/>

CONSTRUCT {
  ?company rdf:type dbo:Company ;
           rdfs:label ?companyLabel ;
           dbo:parentCompany ?parent ;
           dbo:hasSubsidiary ?subsidiary ;
           dbo:hasProduct ?product .

  ?subsidiary rdf:type dbo:Company ;
              rdfs:label ?subsidiaryLabel .

  ?product rdf:type dbo:Product ;
           rdfs:label ?productLabel .
}
WHERE {
  {
    SELECT ?company WHERE {
      ?company rdf:type dbo:Company .
      OPTIONAL { ?subsidiary dbo:parentCompany ?company . }
      OPTIONAL { ?product dbo:manufacturer ?company . }
      
      FILTER EXISTS {
    		?someCompany rdf:type dbo:Company .
    		?someProduct dbo:manufacturer ?someCompany .
  		}
    }
    GROUP BY ?company
    HAVING (COUNT(DISTINCT ?subsidiary) > COUNT(DISTINCT ?product))
    LIMIT 25 #LIMIT 100, 200, 500, 1000
  }

  ?company rdf:type dbo:Company .
  OPTIONAL { ?company rdfs:label ?companyLabel . }
  OPTIONAL { ?company dbo:parentCompany ?parent . }

  {
    # Subsidiaries branch
    OPTIONAL {
      ?subsidiary dbo:parentCompany ?company .
      OPTIONAL { ?subsidiary rdfs:label ?subsidiaryLabel . }
    }
  }
  UNION
  {
    # Products branch (inverse of dbo:manufacturer)
    OPTIONAL {
      ?product dbo:manufacturer ?company .
      OPTIONAL { ?product rdfs:label ?productLabel . }
    }
  }
}

```

#### Individuals (SELECT)
```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?company
WHERE {
  {
    SELECT ?company WHERE {
      ?company rdf:type dbo:Company .
      
      OPTIONAL { ?subsidiary dbo:parentCompany ?company . }
      OPTIONAL { ?product dbo:manufacturer ?company . }
      
      FILTER EXISTS {
    		?someCompany rdf:type dbo:Company .
    		?someProduct dbo:manufacturer ?someCompany .
  		}
    }
    GROUP BY ?company
    HAVING (COUNT(DISTINCT ?subsidiary) > COUNT(DISTINCT ?product))
    LIMIT 25 #LIMIT 100, 200, 500, 1000
  }
  
  ?company rdf:type dbo:Company .
  OPTIONAL { ?subsidiary dbo:parentCompany ?company . }
  OPTIONAL { ?product dbo:manufacturer ?company . }
}
GROUP BY ?company
ORDER BY ?company
```

### Negative Class (N)
*Companies with more products than subsidiaries.*

#### Ontology Graph (CONSTRUCT)
```
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo:  <http://dbpedia.org/ontology/>

CONSTRUCT {
  ?company rdf:type dbo:Company ;
           rdfs:label ?companyLabel ;
           dbo:parentCompany ?parent ;
           dbo:hasSubsidiary ?subsidiary ;
           dbo:hasProduct ?product .

  ?subsidiary rdf:type dbo:Company ;
              rdfs:label ?subsidiaryLabel .

  ?product rdf:type dbo:Product ;
           rdfs:label ?productLabel .
}
WHERE {
  {
    SELECT ?company WHERE {
      ?company rdf:type dbo:Company .
      OPTIONAL { ?subsidiary dbo:parentCompany ?company . }
      OPTIONAL { ?product dbo:manufacturer ?company . }
    }
    GROUP BY ?company
    HAVING (COUNT(DISTINCT ?product) > COUNT(DISTINCT ?subsidiary))
    LIMIT 25 #LIMIT 100, 200, 500, 1000
  }

  ?company rdf:type dbo:Company .
  OPTIONAL { ?company rdfs:label ?companyLabel . }
  OPTIONAL { ?company dbo:parentCompany ?parent . }

  {
    # Subsidiaries branch
    OPTIONAL {
      ?subsidiary dbo:parentCompany ?company .
      OPTIONAL { ?subsidiary rdfs:label ?subsidiaryLabel . }
    }
  }
  UNION
  {
    # Products branch (inverse of dbo:manufacturer)
    OPTIONAL {
      ?product dbo:manufacturer ?company .
      OPTIONAL { ?product rdfs:label ?productLabel . }
    }
  }
}

```

#### Individuals (SELECT)
```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?company
WHERE {
  {
    SELECT ?company WHERE {
      ?company rdf:type dbo:Company .
      
      OPTIONAL { ?subsidiary dbo:parentCompany ?company . }
      OPTIONAL { ?product dbo:manufacturer ?company . }
    }
    GROUP BY ?company
    HAVING (COUNT(DISTINCT ?product) > COUNT(DISTINCT ?subsidiary))
    LIMIT 25 #LIMIT 100, 200, 500, 1000
  }
  
  ?company rdf:type dbo:Company .
  OPTIONAL { ?subsidiary dbo:parentCompany ?company . }
  OPTIONAL { ?product dbo:manufacturer ?company . }
}
GROUP BY ?company
ORDER BY ?company
```


## Part II — Cities, Universities & Museums
**Dataset family:** dbpedia-universities-*

Cities are classified based on nested majority rules:
1. City level: Must have more universities than museums.
2. University level: Universities are "positive" if they have more colleges than campuses.

* **Positive (P):** City has (Universities > Museums) AND at least one "positive" university.
* **Negative (N):** City has (Universities > Museums) BUT zero "positive" universities.

### Positive Class (P)

#### Ontology Graph (CONSTRUCT)
```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

CONSTRUCT {
  ?city rdf:type dbo:City ; 
        rdfs:label ?cityLabel ;
        dbo:hasUniversity ?university ;
        dbo:hasMuseum ?museum .
  
  ?university rdf:type dbo:University ; 
              rdfs:label ?uniLabel ;
              dbo:hasCollege ?college ;
              dbo:hasCampus ?campus .
  
  ?college rdf:type dbo:EducationalInstitution ; rdfs:label ?collegeLabel .
  ?campus rdfs:label ?campusLabel .
  ?museum rdf:type dbo:Museum ; rdfs:label ?museumLabel .
}
WHERE {
  {
    SELECT ?city WHERE {
      # Innere Selektion der Zählwerte
      {
        SELECT ?city (COUNT(DISTINCT ?u) AS ?uniCount) (COUNT(DISTINCT ?m) AS ?museumCount)
        WHERE {
          ?city rdf:type dbo:City .
          OPTIONAL { ?u rdf:type dbo:University ; dbo:city ?city . }
          OPTIONAL { ?m rdf:type dbo:Museum ; dbo:location ?city . }
        }
        GROUP BY ?city
        HAVING (COUNT(DISTINCT ?u) > COUNT(DISTINCT ?m))
      }
      
      # Filter für die zweite Mehrheitsbedingung
      FILTER EXISTS {
        ?uni dbo:city ?city .
        {
          SELECT ?uni WHERE {
            ?uni rdf:type dbo:University .
            OPTIONAL { ?college dbo:university ?uni . }
            OPTIONAL { ?uni dbo:campus ?campus . }
          }
          GROUP BY ?uni
          HAVING (COUNT(DISTINCT ?college) > COUNT(DISTINCT ?campus))
        }
      }
    }
    ORDER BY DESC(?uniCount)
    LIMIT 25 #50,100
  }

  # Daten-Akquise für den Construct
  OPTIONAL { ?city rdfs:label ?cityLabel . FILTER(lang(?cityLabel) = "en") }
  ?university dbo:city ?city .
  {
      SELECT ?university WHERE {
        ?university rdf:type dbo:University .
        OPTIONAL { ?college dbo:university ?university . }
        OPTIONAL { ?university dbo:campus ?campus . }
      }
      GROUP BY ?university
      HAVING (COUNT(DISTINCT ?college) > COUNT(DISTINCT ?campus))
  }
  OPTIONAL { ?university rdfs:label ?uniLabel . FILTER(lang(?uniLabel) = "en") }
  OPTIONAL { ?college dbo:university ?university . OPTIONAL { ?college rdfs:label ?collegeLabel . FILTER(lang(?collegeLabel) = "en") } }
  OPTIONAL { ?university dbo:campus ?campus . OPTIONAL { ?campus rdfs:label ?campusLabel . FILTER(lang(?campusLabel) = "en") } }
  OPTIONAL { ?museum dbo:location ?city . OPTIONAL { ?museum rdfs:label ?museumLabel . FILTER(lang(?museumLabel) = "en") } }
}
```

#### Individuals (SELECT)
```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?city ?uniCount
WHERE {
  # Same First Majority logic
  {
    SELECT ?city (COUNT(DISTINCT ?u) AS ?uniCount) (COUNT(DISTINCT ?m) AS ?museumCount)
    WHERE {
      ?city rdf:type dbo:City .
      OPTIONAL { ?u rdf:type dbo:University ; dbo:city ?city . }
      OPTIONAL { ?m rdf:type dbo:Museum ; dbo:location ?city . }
    }
    GROUP BY ?city
    HAVING (COUNT(DISTINCT ?u) > COUNT(DISTINCT ?m))
  }

  # Same Second Majority logic
  FILTER EXISTS {
    ?uni rdf:type dbo:University ; dbo:city ?city . 
    {
      SELECT ?uni WHERE {
        ?uni rdf:type dbo:University .
        OPTIONAL { ?college dbo:university ?uni . }
        OPTIONAL { ?uni dbo:campus ?campus . }
      }
      GROUP BY ?uni
      HAVING (COUNT(DISTINCT ?college) > COUNT(DISTINCT ?campus))
    }
  }
}
ORDER BY DESC(?uniCount) # Match the Construct Query
LIMIT 25 #50,100
```

### Negative Class (N)

#### Ontology Graph (CONSTRUCT)
```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

CONSTRUCT {
  ?city rdf:type dbo:City ; 
        rdfs:label ?cityLabel ;
        dbo:hasUniversity ?university ;
        dbo:hasMuseum ?museum .
  
  ?university rdf:type dbo:University ; 
              rdfs:label ?uniLabel ;
              dbo:hasCollege ?college ;
              dbo:hasCampus ?campus .
  
  ?college rdf:type dbo:EducationalInstitution ; rdfs:label ?collegeLabel .
  ?campus rdfs:label ?campusLabel .
  ?museum rdf:type dbo:Museum ; rdfs:label ?museumLabel .
}
WHERE {
  {
    SELECT ?city WHERE {
      {
        SELECT ?city (COUNT(DISTINCT ?u) AS ?uniCount) (COUNT(DISTINCT ?m) AS ?museumCount)
        WHERE {
          ?city rdf:type dbo:City .
          OPTIONAL { ?u rdf:type dbo:University ; dbo:city ?city . }
          OPTIONAL { ?m rdf:type dbo:Museum ; dbo:location ?city . }
        }
        GROUP BY ?city
        HAVING (COUNT(DISTINCT ?u) > COUNT(DISTINCT ?m))
      }
      
      # Die Stadt ist NEGATIV, wenn KEINE ihrer Unis die positive Bedingung erfüllt
      FILTER NOT EXISTS {
        ?uni dbo:city ?city .
        {
          SELECT ?uni WHERE {
            ?uni rdf:type dbo:University .
            OPTIONAL { ?college dbo:university ?uni . }
            OPTIONAL { ?uni dbo:campus ?campus . }
          }
          GROUP BY ?uni
          HAVING (COUNT(DISTINCT ?college) > COUNT(DISTINCT ?campus))
        }
      }
    }
    ORDER BY DESC(?uniCount)
    LIMIT 25 #50,100
  }

  # Daten-Akquise: Hier nehmen wir JETZT ALLE Unis der Stadt auf
  OPTIONAL { ?city rdfs:label ?cityLabel . FILTER(lang(?cityLabel) = "en") }
  
  ?university dbo:city ?city .
  ?university rdf:type dbo:University . 
  
  OPTIONAL { ?university rdfs:label ?uniLabel . FILTER(lang(?uniLabel) = "en") }
  
  # Wir zeigen dem Learner alle Colleges und Campuses, damit er sieht, 
  # dass hier die Majority-Bedingung eben NICHT zutrifft.
  OPTIONAL {
    ?college dbo:university ?university .
    OPTIONAL { ?college rdfs:label ?collegeLabel . FILTER(lang(?collegeLabel) = "en") }
  }
  OPTIONAL {
    ?university dbo:campus ?campus .
    OPTIONAL { ?campus rdfs:label ?campusLabel . FILTER(lang(?campusLabel) = "en") }
  }
  OPTIONAL {
    ?museum dbo:location ?city .
    OPTIONAL { ?museum rdfs:label ?museumLabel . FILTER(lang(?museumLabel) = "en") }
  }
}
```

#### Individuals (SELECT)
```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT DISTINCT ?city ?uniCount
WHERE {
  # 1. Bedingung bleibt: Mehr Unis als Museen
  {
    SELECT ?city (COUNT(DISTINCT ?u) AS ?uniCount) (COUNT(DISTINCT ?m) AS ?museumCount)
    WHERE {
      ?city rdf:type dbo:City .
      OPTIONAL { ?u rdf:type dbo:University ; dbo:city ?city . }
      OPTIONAL { ?m rdf:type dbo:Museum ; dbo:location ?city . }
    }
    GROUP BY ?city
    HAVING (COUNT(DISTINCT ?u) > COUNT(DISTINCT ?m))
  }

  # 2. Umkehrung: Es darf KEINE Uni existieren, die mehr Colleges als Campuses hat
  FILTER NOT EXISTS {
    ?uni rdf:type dbo:University ; dbo:city ?city . 
    {
      SELECT ?uni WHERE {
        ?uni rdf:type dbo:University .
        OPTIONAL { ?college dbo:university ?uni . }
        OPTIONAL { ?uni dbo:campus ?campus . }
      }
      GROUP BY ?uni
      HAVING (COUNT(DISTINCT ?college) > COUNT(DISTINCT ?campus))
    }
  }
}
ORDER BY DESC(?uniCount)
LIMIT 25 #50,100
```
