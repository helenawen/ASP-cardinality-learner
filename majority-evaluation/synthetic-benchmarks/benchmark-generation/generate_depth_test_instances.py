def generate_depth_test(depth_n: int, base_uri="http://example.org/tree#"):
    rdf = [f'''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:owl="http://www.w3.org/2002/07/owl#"
         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
         xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
         xmlns="{base_uri}"
         xml:base="{base_uri}">

  <owl:Ontology rdf:about="{base_uri}">
    <rdfs:comment>Ontology representing a hierarchical tree with nodes colored A0 and A1, extended to depth {depth_n} (n1->...->n{depth_n}->branches).</rdfs:comment>
  </owl:Ontology>

  <owl:Class rdf:about="#Node"/>
  <owl:Class rdf:about="#A0"/>
  <owl:Class rdf:about="#A1"/>

  <owl:ObjectProperty rdf:about="#hasChild">
    <rdfs:domain rdf:resource="#Node"/>
    <rdfs:range rdf:resource="#Node"/>
  </owl:ObjectProperty>''']

    # n path nodes
    for i in range(1, depth_n):
        child = i + 1
        rdf.append(f'''
  <Node rdf:about="#n{i}">
    <rdf:type rdf:resource="#A0"/>
    <hasChild rdf:resource="#n{child}"/>
  </Node>''')

    # n last node with three children
    last = depth_n
    n_children = [(f"n{last+1}", "A0"), (f"n{last+2}", "A0"), (f"n{last+3}", "A1")]
    rdf.append(f'''
  <Node rdf:about="#n{last}">
    <rdf:type rdf:resource="#A0"/>''')
    for child_name, _ in n_children:
        rdf.append(f'    <hasChild rdf:resource="#{child_name}"/>')
    rdf.append('  </Node>')

    # n leaf children
    for name, ctype in n_children:
        rdf.append(f'  <Node rdf:about="#{name}"><rdf:type rdf:resource="#{ctype}"/></Node>')

    # m path nodes
    for i in range(1, depth_n):
        child = i + 1
        rdf.append(f'''
  <Node rdf:about="#m{i}">
    <rdf:type rdf:resource="#A0"/>
    <hasChild rdf:resource="#m{child}"/>
  </Node>''')

    # m last node with three children
    m_children = [(f"m{last+1}", "A0"), (f"m{last+2}", "A1"), (f"m{last+3}", "A1")]
    rdf.append(f'''
  <Node rdf:about="#m{last}">
    <rdf:type rdf:resource="#A0"/>''')
    for child_name, _ in m_children:
        rdf.append(f'    <hasChild rdf:resource="#{child_name}"/>')
    rdf.append('  </Node>')

    # m leaf children
    for name, ctype in m_children:
        rdf.append(f'  <Node rdf:about="#{name}"><rdf:type rdf:resource="#{ctype}"/></Node>')

    rdf.append('</rdf:RDF>')

    return '\n'.join(rdf)

# Example usage
if __name__ == "__main__":
    depth_n = int(input("Enter depth of the main path: "))
    rdf_content = generate_depth_test(depth_n)
    output_file = f"depth-{depth_n}.owl"
    with open(output_file, "w") as f:
        f.write(rdf_content)
    print(f"OWL file '{output_file}' generated for depth {depth_n}.")
