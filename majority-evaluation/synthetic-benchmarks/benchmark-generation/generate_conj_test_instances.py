def generate_rdf_owl(num_concepts: int, base_uri="http://example.com/test#"):
    # Number of children = num_concepts * 2
    num_children = num_concepts * 2

    # Generate concept names
    concepts = [f"A{i}" for i in range(num_concepts)]

    # Start RDF/XML (OWL)
    rdf = ['''<?xml version="1.0"?>
<rdf:RDF xmlns="urn:absolute:test#" xml:base="urn:absolute:test"
         xmlns:owl="http://www.w3.org/2002/07/owl#"
         xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:xml="http://www.w3.org/XML/1998/namespace"
         xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
         xmlns:test="{}">

  <owl:Ontology rdf:about="urn:absolute:test"/>'''.format(base_uri)]

    # Declare classes
    for c in concepts:
        rdf.append(f'  <owl:Class rdf:about="{base_uri}{c}"/>')

    # Object property
    rdf.append(f'  <owl:ObjectProperty rdf:about="{base_uri}r"/>')

    # Helper function for a child
    def child_node_xml(name, concept_list):
        types_xml = ''.join([f'\n    <rdf:type rdf:resource="{base_uri}{c}"/>' for c in concept_list])
        return f'  <owl:NamedIndividual rdf:about="{base_uri}{name}">{types_xml}\n  </owl:NamedIndividual>'

    # n node and children
    rdf.append(f'  <owl:NamedIndividual rdf:about="{base_uri}n">')
    for i in range(1, num_children + 1):
        rdf.append(f'    <test:r rdf:resource="{base_uri}n{i}"/>')
    rdf.append('  </owl:NamedIndividual>')

    for i in range(1, num_children + 1):
        rdf.append(child_node_xml(f"n{i}", concepts))

    # m node and children
    rdf.append(f'  <owl:NamedIndividual rdf:about="{base_uri}m">')
    for i in range(1, num_children + 1):
        rdf.append(f'    <test:r rdf:resource="{base_uri}m{i}"/>')
    rdf.append('  </owl:NamedIndividual>')

    # m children
    half = num_children // 2
    for i in range(1, num_children + 1):
        if i <= half:
            # Full conjunction
            rdf.append(child_node_xml(f"m{i}", concepts))
        else:
            # Missing one concept sequentially
            missing_idx = (i - half - 1) % num_concepts
            concept_list = [c for idx, c in enumerate(concepts) if idx != missing_idx]
            rdf.append(child_node_xml(f"m{i}", concept_list))

    rdf.append('</rdf:RDF>')
    return '\n'.join(rdf)


# Example usage
if __name__ == "__main__":
    num_concepts = int(input("Enter number concept names: "))
    rdf_content = generate_rdf_owl(num_concepts)

    output_file = f"conj-{num_concepts}.owl"
    with open(output_file, "w") as f:
        f.write(rdf_content)

    print(f"OWL file '{output_file}' generated with {num_concepts} concepts and {num_concepts * 2} children per node.")
