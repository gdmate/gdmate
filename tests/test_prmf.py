"""
Test for prmf module
"""

from gdmate.parameters import prmf
import io
import sys
import tempfile


def test_combine_dicts():
    """ Test combine_dicts function """

    # create two dictionaries to be combined
    dict_1 = dict({'Global parameters': {'Dimension': {'value': '2'},
                                         'End time': {'value': '5e6'},
                                         'Output directory': {'value': 'output'}},
                   'Geometry model': {'Model name': {'value': 'box'},
                                      'Box': {'X extent': {'value': '4.2e6'},
                                              'Y extent': {'value': '3e6'}}},
                   'Mesh refinement': {'Initial global refinement': {'value': '3'},
                                       'Initial adaptive refinement': {'value': '0'},
                                       'Time steps between refinement': {'value': '0'}}})

    dict_2 = dict({'Global parameters': {'Dimension': {'value': '2'},
                                         'Use years in output instead of seconds': {'value': 'true'}},
                   'Geometry model': {'Model name': {'value': 'box'},
                                      'Box': {'X extent': {'value': '4.2e6'}}}})

    # create the expected dictionary from combining dict_1 and dict_3
    dict_3 = dict({'Global parameters': {'Dimension': {'value': '2'},
                                         'End time': {'value': '5e6'},
                                         'Output directory': {'value': 'output'},
                                         'Use years in output instead of seconds': {'value': 'true'}},
                   'Geometry model': {'Model name': {'value': 'box'},
                                      'Box': {'X extent': {'value': '4.2e6'},
                                              'Y extent': {'value': '3e6'}}},
                   'Mesh refinement': {'Initial global refinement': {'value': '3'},
                                       'Initial adaptive refinement': {'value': '0'},
                                       'Time steps between refinement': {'value': '0'}}})

    # combine dict_1 and dict_2
    combine_dicts(dict_1, dict_2)

    # test that now dict_2 == dict_3
    assert dict_2 == dict_3


def test_rekey():
    """ Test rekey function """

    # create a dictionary for the test
    dict_1 = dict({'Global_20parameters': {'Dimension': {'value': '2'},
                                           'End_20time': {'value': '5e6'},
                                           'Output_20directory': {'value': 'output'},
                                           'Max_20nonlinear_20iterations_20in_20pre_2drefinement': {'value': '0'}},
                   'Geometry_20model': {'Model_20name': {'value': 'box'},
                                        'Box': {'X_20extent': {'value': '4.2e6'},
                                                'Y_20extent': {'value': '3e6'}}},
                   'Mesh_20refinement': {'Initial_20global_20refinement': {'value': '3'},
                                         'Initial_20adaptive_20refinement': {'value': '0'},
                                         'Time_20steps_20between_20refinement': {'value': '0'}}})

    # the expected dictionary after updating the keys
    dict_2 = dict({'Global parameters': {'Dimension': {'value': '2'},
                                         'End time': {'value': '5e6'},
                                         'Output directory': {'value': 'output'},
                                         'Max nonlinear iterations in pre-refinement': {'value': '0'}},
                   'Geometry model': {'Model name': {'value': 'box'},
                                      'Box': {'X extent': {'value': '4.2e6'},
                                              'Y extent': {'value': '3e6'}}},
                   'Mesh refinement': {'Initial global refinement': {'value': '3'},
                                       'Initial adaptive refinement': {'value': '0'},
                                       'Time steps between refinement': {'value': '0'}}})
    dict_3 = dict({})
    rekey(dict_1, dict_3)

    assert dict_3 == dict_2


def test_import_prm_library():
    prm_library = dict({})

    import_prm_library(prm_library)

    assert prm_library != {}


def test_prmf_to_prmlist():
    """ Test prmf_to_prmlist function """

    # file to be used for the test
    f = 'assets/short_test_f.prm'

    # expected returned list
    check_lines_list = ['set Dimension                              = 2',
                        'set Use years in output instead of seconds = true',
                        'set End time                               = 3e10',
                        'set Output directory                       = output',
                        'subsection Geometry model',
                        'set Model name = box',
                        'subsection Box',
                        'set X extent = 4.2e6',
                        'set Y extent = 3e6',
                        'end',
                        'end']

    lines_list = prmf_to_prmlist(f)

    assert lines_list == check_lines_list


def test_prmlist_to_prmdict():
    """ Test prmlist_to_prmdict function """

    # create list for the test
    lines_list = ['set Dimension                              = 2',
                  'set Use years in output instead of seconds = true',
                  'set End time                               = 3e10',
                  'set Output directory                       = output',
                  'subsection Geometry model',
                  'set Model name = box',
                  'subsection Box',
                  'set X extent = 4.2e6',
                  'set Y extent = 3e6',
                  'end',
                  'end']

    # expected return dictionary

    out_dict = dict({'Global parameters': {'Dimension': {'value': '2'},
                                           'Use years in output instead of seconds': {'value': 'true'},
                                           'End time': {'value': '3e10'},
                                           'Output directory': {'value': 'output'}},
                     'Geometry model': {'Model name': {'value': 'box'},
                                        'Box': {'X extent': {'value': '4.2e6'},
                                                'Y extent': {'value': '3e6'}}}})

    test_dict = prmlist_to_prmdict(lines_list)

    assert test_dict == out_dict


def test_check_prmdict_diff():
    """ Test check_prmdict_diff function """

    # creat two dictionary for comparison test
    dict_1 = dict({'Global parameters': {'Dimension': {'value': '2'},
                                         'Use years in output instead of seconds': {'value': 'true'},
                                         'End time': {'value': '4e10'},
                                         'Output directory': {'value': 'output'}},
                   'Geometry model': {'Model name': {'value': 'box'},
                                      'Box': {'X extent': {'value': '4.2e6'},
                                              'Y extent': {'value': '3e6'}}}})
    dict_2 = dict({'Global parameters': {'Dimension': {'value': '2'},
                                         'Use years in output instead of seconds': {'value': 'true'},
                                         'End time': {'value': '3e10'},
                                         'Output directory': {'value': 'output'}},
                   'Geometry model': {'Model name': {'value': 'box'},
                                      'Box with lithosphere boundary indicators': {'X extent': {'value': '4.2e6'},
                                                                                   'Y extent': {'value': '3e6'}}}})
    # create the expected string to be printed
    expected_output = '<| Global parameters| End time>\n' \
                      '    value = 4e10 (input 1)\n' \
                      '    value = 3e10 (input 2) \n\n' \
                      '<| Geometry model| Box> found in input 1 but not in input 2\n\n'

    # create StringIO object
    output = io.StringIO()
    # redirect stdout
    sys.stdout = output
    # run check_prmdict_diff function
    check_prmdict_diff(dict_1, dict_2)
    # reset redirect
    sys.stdout = sys.__stdout__

    assert output.getvalue() == expected_output


def test_load_prmf():
    """ Test load_prmf function """

    # creat the expect dictionary from loading 'assets/short_test_f.prm'
    expected_dict = dict({'Global parameters': {'Dimension': {'value': '2'},
                                                'Use years in output instead of seconds': {'value': 'true'},
                                                'End time': {'value': '3e10'},
                                                'Output directory': {'value': 'output'}},
                          'Geometry model': {'Model name': {'value': 'box'},
                                             'Box': {'X extent': {'value': '4.2e6'},
                                                     'Y extent': {'value': '3e6'}}}})
    # run load_prmf function
    d = load_prmf('assets/short_test_f.prm')

    assert d == expected_dict


def test_check_prmf_diff():
    """ Test check_prmdict_diff function """

    # create the expected string to be printed
    expected_output = '<| Global parameters| End time>\n' \
                      '    value = 3e10 (input 1)\n' \
                      '    value = 5e10 (input 2) \n\n' \
                      '<| Initial temperature model| Function| Function constants>\n' \
                      '    value = p=-0.01, L=4.2e6, D=3e6, pi=3.1415926536, k=1, T_top=273, T_bottom=3600 (input 1)\n' \
                      '    value = p=-0.01, L=4.2e6, D=3e6, pi=3.1415926536, k=1, T_top=293, T_bottom=3600 (input 2) \n\n' \
                      '<| Postprocess| List of postprocessors>\n' \
                      '    value = velocity statistics, temperature statistics, heat flux statistics, visualization, particles, basic statistics (input 1)\n' \
                      '    value = velocity statistics, temperature statistics, heat flux statistics, visualization, basic statistics (input 2) \n\n' \
                      '<| Postprocess| Particles> found in input 1 but not in input 2\n\n'

    # create StringIO object
    output = io.StringIO()
    # redirect stdout
    sys.stdout = output
    # run check_prmdict_diff function
    check_prmf_diff('assets/test_f1.prm', 'assets/test_f2.prm')
    # reset redirect
    sys.stdout = sys.__stdout__

    assert output.getvalue() == expected_output


def test_sprint_prmdict():
    """ Test sprint_prmdict function """

    # create a dictionary
    dict_1 = dict({'Global parameters': {'Dimension': {'value': '2'},
                                         'Use years in output instead of seconds': {'value': 'true'},
                                         'End time': {'value': '4e10'},
                                         'Output directory': {'value': 'output'}},
                   'Geometry model': {'Model name': {'value': 'box'},
                                      'Box': {'X extent': {'value': '4.2e6'},
                                              'Y extent': {'value': '3e6'}}}})
    # create a string with the expected output
    expected_output = 'set Dimension = 2\n' \
                      'set Use years in output instead of seconds = true\n' \
                      'set End time = 4e10\n' \
                      'set Output directory = output\n' \
                      'subsection Geometry model\n' \
                      '  set Model name = box\n' \
                      '  subsection Box\n' \
                      '    set X extent = 4.2e6\n' \
                      '    set Y extent = 3e6\n' \
                      '  end\n' \
                      'end\n'

    # create StringIO object
    output = io.StringIO()
    # redirect stdout
    sys.stdout = output
    # run check_prmdict_diff function
    sprint_prmdict(dict_1)
    # reset redirect
    sys.stdout = sys.__stdout__

    assert output.getvalue() == expected_output


def test_format_prmdict():
    """ Test format_prmdict function """

    # create a dictionary
    dict_1 = dict({'Global parameters': {'Dimension': {'value': '2'},
                                         'Use years in output instead of seconds': {'value': 'true'},
                                         'End time': {'value': '4e10'},
                                         'Output directory': {'value': 'output'}},
                   'Geometry model': {'Model name': {'value': 'box'},
                                      'Box': {'X extent': {'value': '4.2e6'},
                                              'Y extent': {'value': '3e6'}}}})
    # create the expected output list
    expected_list = ['set Dimension = 2',
                     'set Use years in output instead of seconds = true',
                     'set End time = 4e10',
                     'set Output directory = output',
                     'subsection Geometry model',
                     '  set Model name = box',
                     '  subsection Box',
                     '    set X extent = 4.2e6',
                     '    set Y extent = 3e6',
                     '  end',
                     'end']
    # create empty list to test function
    output_list = []
    # test function
    format_prmdict(dict_1, output_list)

    assert output_list == expected_list


def test_write_prmdict():
    """ Test write_prmdict function """
    # create a dictionary
    dict_1 = dict({'Global parameters': {'Dimension': {'value': '2'}}})
    # create a temporary file to save output
    tmpf = tempfile.NamedTemporaryFile(mode='w+')

    write_prmdict(dict_1, tmpf.name)

    assert tmpf.read() == 'set Dimension = 2\n'


def test_prmname_check():
    """ Test prmname_check function """

    # create a dictionary
    dict_1 = dict({'Global parameters': {'Dimensions': {'value': '2'},
                                         'Use years in output instead of seconds': {'value': 'true'},
                                         'End time': {'value': '4e10'},
                                         'Output directory': {'value': 'output'}},
                   'Geometry model': {'Model name': {'value': 'box'},
                                      'Box': {'X extent': {'value': '4.2e6'},
                                              'Y extent': {'value': '3e6'}}}})

    # create StringIO object
    output = io.StringIO()
    # redirect stdout
    sys.stdout = output
    # run check_prmdict_diff function
    prmname_check(dict_1)
    # reset redirect
    sys.stdout = sys.__stdout__

    assert output.getvalue() == 'Unrecognised parameters: \n\t-> Dimensions\n'
