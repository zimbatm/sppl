# Copyright 2020 MIT Probabilistic Computing Project.
# See LICENSE.txt

import pytest

from numpy import linspace

from spn.distributions import bernoulli
from spn.distributions import beta
from spn.distributions import randint
from spn.distributions import uniform

from spn.interpreter import For
from spn.interpreter import IfElse
from spn.interpreter import Sample
from spn.interpreter import Sequence
from spn.interpreter import Switch
from spn.interpreter import Transform
from spn.interpreter import Variable
from spn.interpreter import VariableArray

simAll   = Variable('simAll')
sim      = VariableArray('sim', 5)
p1       = VariableArray('p1', 5)
p2       = VariableArray('p2', 5)
clickA   = VariableArray('clickA', 5)
clickB   = VariableArray('clickB', 5)

ns = 5
nd = ns - 1

def get_command_randint():
    return Sequence(
        Sample(simAll, randint(low=0, high=ns)),
        For(0, 5, lambda k:
            Switch (simAll, 'eq', range(0, ns), lambda i:
                Sequence (
                    Sample (sim[k], bernoulli(p=i/nd)),
                    Sample (p1[k], randint(low=0, high=ns)),
                    IfElse(
                        sim[k] << {1},
                            Sequence(
                                Transform (p2[k], p1[k]),
                                Switch (p1[k], 'eq', range(ns), lambda j:
                                    Sequence(
                                        Sample(clickA[k], bernoulli(p=i/nd)),
                                        Sample(clickB[k], bernoulli(p=i/nd))))),
                        True,
                            Sequence(
                                Sample (p2[k], randint(low=0, high=ns)),
                                Switch (p1[k], 'eq', range(ns), lambda j:
                                      Sample(clickA[k], bernoulli(p=j/nd))),
                                Switch (p2[k], 'eq', range(ns), lambda j:
                                      Sample (clickB[k], bernoulli(p=j/nd)))))))))

def get_command_beta():
    return Sequence(
        Sample(simAll, beta(a=2, b=3)),
        For(0, 5, lambda k:
            Switch (simAll, 'lte', linspace(0, 1, ns), lambda i:
                Sequence (
                    Sample (sim[k], bernoulli(p=i)),
                    Sample (p1[k], uniform()),
                    IfElse(
                        sim[k] << {1},
                            Sequence(
                                Transform (p2[k], p1[k]),
                                Switch (p1[k], 'lte', linspace(0, 1, ns), lambda j:
                                    Sequence(
                                        Sample(clickA[k], bernoulli(p=i)),
                                        Sample(clickB[k], bernoulli(p=i))))),
                        True,
                            Sequence(
                                Sample (p2[k], uniform()),
                                Switch (p1[k], 'lte', linspace(0, 1, ns), lambda j:
                                      Sample(clickA[k], bernoulli(p=j))),
                                Switch (p2[k], 'lte', linspace(0, 1, ns), lambda j:
                                      Sample (clickB[k], bernoulli(p=j)))))))))

@pytest.mark.parametrize('get_command', [get_command_randint, get_command_beta])
def test_clickgraph_crash__ci_(get_command):
    command = get_command()
    model = command.interpret()
    model_condition = model.condition(
            (clickA[0] << {1}) & (clickB[0] << {1})
        &   (clickA[1] << {1}) & (clickB[1] << {1})
        &   (clickA[2] << {1}) & (clickB[2] << {1})
        &   (clickA[3] << {0}) & (clickB[3] << {0})
        &   (clickA[4] << {0}) & (clickB[4] << {0}))
    probabilities = [model_condition.prob(simAll << {i}) for i in range(ns)]
    assert all(p <= probabilities[nd-1] for p in probabilities)
