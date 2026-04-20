PYTHON=python
SPELL=$(PYTHON) spell_cli.py

all: family courses hobbies father hard1 hard5 yago10_2 yago10_19 owl2bench1 owl2bench3 owl2bench4 color1 color2 color3 color4 color-alt-1 color-alt-2 color-alt-3 color-alt-4 color-alt-5 color-alt-6 color-alt-9 color-alt-10 conj1 conj2 conj3 conj4 debug

chemistry:
	$(SPELL) tests/chemistry-example/chemistry.owl tests/chemistry-example/P.txt tests/chemistry-example/N.txt

family:
	$(SPELL) tests/family-example/family.owl tests/family-example/P.txt tests/family-example/N.txt

courses:
	$(SPELL) tests/courses-example/courses.owl tests/courses-example/P.txt tests/courses-example/N.txt

hobbies:
	$(SPELL) tests/hobbies-example/hobbies.owl tests/hobbies-example/P.txt tests/hobbies-example/N.txt

father:
	$(SPELL) tests/father-example/father.owl tests/father-example/P.txt tests/father-example/N.txt

hard1:
	$(SPELL) tests/test-hard-deep-conj-1/owl/data/test-hard-deep-conj-1.owl tests/test-hard-deep-conj-1/owl/lp/1/pos.txt tests/test-hard-deep-conj-1/owl/lp/1/neg.txt

hard5:
	$(SPELL) tests/test-hard-deep-conj-5/owl/data/test-hard-deep-conj-5.owl tests/test-hard-deep-conj-5/owl/lp/1/pos.txt tests/test-hard-deep-conj-5/owl/lp/1/neg.txt

yago10_2:
	$(SPELL) tests/yago-gen-test-10-2/owl/data/yago-gen-test-10-2.owl tests/yago-gen-test-10-2/owl/lp/1/pos.txt tests/yago-gen-test-10-2/owl/lp/1/neg.txt

yago10_19:
	$(SPELL) tests/yago-gen-test-10-19/owl/data/yago-gen-test-10-19.owl tests/yago-gen-test-10-19/owl/lp/1/pos.txt tests/yago-gen-test-10-19/owl/lp/1/neg.txt

owl2bench1:
	$(SPELL) tests/owl2bench-1/owl/data/owl2bench-1.owl tests/owl2bench-1/owl/lp/1/pos.txt tests/owl2bench-1/owl/lp/1/neg.txt

owl2bench3:
	$(SPELL) tests/owl2bench-3/owl/data/owl2bench-3.owl tests/owl2bench-3/owl/lp/1/pos.txt tests/owl2bench-3/owl/lp/1/neg.txt

owl2bench4:
	$(SPELL) tests/owl2bench-4/owl/data/owl2bench-4.owl tests/owl2bench-4/owl/lp/1/pos.txt tests/owl2bench-4/owl/lp/1/neg.txt

color1:
	$(SPELL) tests/color-example/color-depth1.owl tests/color-example/P.txt tests/color-example/N-depth1.txt

color2:
	$(SPELL) tests/color-example/color-depth2.owl tests/color-example/P.txt tests/color-example/N-depth2.txt

color3:
	$(SPELL) tests/color-example/color-depth3.owl tests/color-example/P.txt tests/color-example/N-depth3.txt

color4:
	$(SPELL) tests/color-example/color-depth4.owl tests/color-example/P.txt tests/color-example/N-depth4.txt

color-alt-1:
	$(SPELL) tests/color-example/color-alt-depth1.owl tests/color-example/P.txt tests/color-example/N.txt

color-alt-2:
	$(SPELL) tests/color-example/color-alt-depth2.owl tests/color-example/P.txt tests/color-example/N.txt

color-alt-3:
	$(SPELL) tests/color-example/color-alt-depth3.owl tests/color-example/P.txt tests/color-example/N.txt

color-alt-4:
	$(SPELL) tests/color-example/color-alt-depth4.owl tests/color-example/P.txt tests/color-example/N.txt

color-alt-5:
	$(SPELL) tests/color-example/color-alt-depth5.owl tests/color-example/P.txt tests/color-example/N.txt

color-alt-6:
	$(SPELL) tests/color-example/color-alt-depth6.owl tests/color-example/P.txt tests/color-example/N.txt

conj1:
	$(SPELL) tests/conjunction-example/conj1.owl tests/conjunction-example/P.txt tests/conjunction-example/N.txt

conj2:
	$(SPELL) tests/conjunction-example/conj2.owl tests/conjunction-example/P.txt tests/conjunction-example/N.txt

conj3:
	$(SPELL) tests/conjunction-example/conj3.owl tests/conjunction-example/P.txt tests/conjunction-example/N.txt

conj4:
	$(SPELL) tests/conjunction-example/conj4.owl tests/conjunction-example/P.txt tests/conjunction-example/N.txt

debug:
	$(SPELL) tests/debug-example/debug.owl tests/debug-example/P.txt tests/debug-example/N.txt

depth-1:
	$(SPELL) tests/depth-test-instances/depth-1.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-2:
	$(SPELL) tests/depth-test-instances/depth-2.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-3:
	$(SPELL) tests/depth-test-instances/depth-3.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-4:
	$(SPELL) tests/depth-test-instances/depth-4.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-5:
	$(SPELL) tests/depth-test-instances/depth-5.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-6:
	$(SPELL) tests/depth-test-instances/depth-6.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-7:
	$(SPELL) tests/depth-test-instances/depth-7.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-8:
	$(SPELL) tests/depth-test-instances/depth-8.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-9:
	$(SPELL) tests/depth-test-instances/depth-9.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-10:
	$(SPELL) tests/depth-test-instances/depth-10.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-11:
	$(SPELL) tests/depth-test-instances/depth-11.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-12:
	$(SPELL) tests/depth-test-instances/depth-12.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-13:
	$(SPELL) tests/depth-test-instances/depth-13.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-14:
	$(SPELL) tests/depth-test-instances/depth-14.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

depth-15:
	$(SPELL) tests/depth-test-instances/depth-15.owl tests/depth-test-instances/P.txt tests/depth-test-instances/N.txt

conj-1:
	$(SPELL) tests/conjunction-test-instances/conj-1.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-2:
	$(SPELL) tests/conjunction-test-instances/conj-2.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-3:
	$(SPELL) tests/conjunction-test-instances/conj-3.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-4:
	$(SPELL) tests/conjunction-test-instances/conj-4.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-5:
	$(SPELL) tests/conjunction-test-instances/conj-5.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-6:
	$(SPELL) tests/conjunction-test-instances/conj-6.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-7:
	$(SPELL) tests/conjunction-test-instances/conj-7.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-8:
	$(SPELL) tests/conjunction-test-instances/conj-8.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-9:
	$(SPELL) tests/conjunction-test-instances/conj-9.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-10:
	$(SPELL) tests/conjunction-test-instances/conj-10.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-11:
	$(SPELL) tests/conjunction-test-instances/conj-11.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-12:
	$(SPELL) tests/conjunction-test-instances/conj-12.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-13:
	$(SPELL) tests/conjunction-test-instances/conj-13.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-14:
	$(SPELL) tests/conjunction-test-instances/conj-14.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt

conj-15:
	$(SPELL) tests/conjunction-test-instances/conj-15.owl tests/conjunction-test-instances/P.txt tests/conjunction-test-instances/N.txt
