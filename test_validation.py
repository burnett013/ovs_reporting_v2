from utils import llm_parser

def test_validation():
    print("Testing validation logic...")
    
    # Test GR validation
    gr_programs = [
        {"program_name": "Accountancy", "credential": "M.S.A.A.", "page_number": 100}, # Valid
        {"program_name": "Accountancy", "credential": "B.S.", "page_number": 100},     # Invalid (starts with B.)
        {"program_name": "Biology", "credential": "Ph.D.", "page_number": 100},        # Valid
        {"program_name": "Art", "credential": "Minor", "page_number": 100},            # Invalid (Minor)
        {"program_name": "Business", "credential": "M.B.A.", "page_number": 100},      # Valid (starts with M.)
    ]
    
    valid_gr = llm_parser.validate_catalog_type(gr_programs, 'gr')
    print(f"GR Input: {len(gr_programs)}, Output: {len(valid_gr)}")
    for p in valid_gr:
        print(f"  Kept: {p['program_name']} ({p['credential']})")
        
    assert len(valid_gr) == 3
    assert any(p['credential'] == "M.S.A.A." for p in valid_gr)
    assert any(p['credential'] == "Ph.D." for p in valid_gr)
    assert any(p['credential'] == "M.B.A." for p in valid_gr)
    assert not any(p['credential'] == "B.S." for p in valid_gr)
    
    # Test UG validation
    ug_programs = [
        {"program_name": "History", "credential": "B.A.", "page_number": 100},         # Valid
        {"program_name": "History", "credential": "M.A.", "page_number": 100},         # Invalid (starts with M.)
        {"program_name": "Math", "credential": "Minor", "page_number": 100},           # Valid
        {"program_name": "Physics", "credential": "Ph.D.", "page_number": 100},        # Invalid (starts with Ph.D.)
        {"program_name": "Criminology", "credential": "Ph.D", "page_number": 100},     # Invalid (Ph.D no dot)
        {"program_name": "Education", "credential": "Ed.S.", "page_number": 100},      # Invalid (Ed.S.)
        {"program_name": "Pharmacy", "credential": "Pharm.D.", "page_number": 100},    # Invalid (Pharm.D.)
        {"program_name": "Japanese", "credential": "Certificate", "page_number": 100}, # Valid (Certificate is UG)
        {"program_name": "Biomedical Sciences", "credential": "B.S.", "page_number": 100, "original_text": "B.S. in Biomedical Sciences"}, # Invalid (Cred first)
    ]
    
    valid_ug = llm_parser.validate_catalog_type(ug_programs, 'ug')
    print(f"UG Input: {len(ug_programs)}, Output: {len(valid_ug)}")
    for p in valid_ug:
        print(f"  Kept: {p['program_name']} ({p['credential']})")

    assert len(valid_ug) == 3
    assert any(p['credential'] == "B.A." for p in valid_ug)
    assert any(p['credential'] == "Certificate" for p in valid_ug)
    assert not any(p['credential'] == "Ph.D" for p in valid_ug)
    assert not any(p['credential'] == "Ed.S." for p in valid_ug)

    # Test GR validation for Certificate
    gr_programs_cert = [
        {"program_name": "AI", "credential": "Graduate Certificate", "page_number": 100}, # Valid
        {"program_name": "Japanese", "credential": "Certificate", "page_number": 100},    # Invalid (UG Certificate)
    ]
    valid_gr_cert = llm_parser.validate_catalog_type(gr_programs_cert, 'gr')
    print(f"GR Cert Input: {len(gr_programs_cert)}, Output: {len(valid_gr_cert)}")
    for p in valid_gr_cert:
        print(f"  Kept: {p['program_name']} ({p['credential']})")
    
    assert len(valid_gr_cert) == 1
    assert valid_gr_cert[0]['credential'] == "Graduate Certificate"

    print("Validation logic passed!")

if __name__ == "__main__":
    test_validation()
