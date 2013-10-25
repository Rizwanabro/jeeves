import unittest
import macropy.activate
from sourcetrans.macro_module import macros, jeeves
import JeevesLib

class TestClass:
  @jeeves
  def __init__(self, a, b):
    self.a = a
    self.b = b

class TestClassMethod:
  @jeeves
  def __init__(self, a, b):
    self.a = a
    self.b = b
  @jeeves
  def add_a_to_b(self):
    self.b = self.a + self.b
  @jeeves
  def return_sum(self):
    return self.a + self.b

class TestSourceTransform(unittest.TestCase):
  def setUp(self):
    # reset the Jeeves state
    JeevesLib.init()

  @jeeves
  def test_restrict_all_permissive(self):
    x = JeevesLib.mkLabel('x')
    JeevesLib.restrict(x, lambda _: True)
    xConcrete = JeevesLib.concretize(None, x)
    self.assertTrue(xConcrete)

  @jeeves
  def test_restrict_all_restrictive(self):
    x = JeevesLib.mkLabel('x')
    JeevesLib.restrict(x, lambda _: False)
    xConcrete = JeevesLib.concretize(None, x)
    self.assertFalse(xConcrete)

  @jeeves
  def test_restrict_with_context(self):
    x = JeevesLib.mkLabel('x')
    JeevesLib.restrict(x, lambda y: y == 2)

    xConcrete = JeevesLib.concretize(2, x)
    self.assertTrue(xConcrete)

    xConcrete = JeevesLib.concretize(3, x)
    self.assertFalse(xConcrete)

  @jeeves
  def test_restrict_with_sensitive_value(self):
    x = JeevesLib.mkLabel('x')
    JeevesLib.restrict(x, lambda y: y == 2)
    value = JeevesLib.mkSensitive(x, 42, 41)

    valueConcrete = JeevesLib.concretize(2, value)
    self.assertEquals(valueConcrete, 42)

    valueConcrete = JeevesLib.concretize(1, value)
    self.assertEquals(valueConcrete, 41)

  @jeeves
  def test_restrict_with_cyclic(self):
    jl = JeevesLib

    # use the value itself as the context
    x = jl.mkLabel('x')
    jl.restrict(x, lambda ctxt : ctxt == 42)

    value = jl.mkSensitive(x, 42, 20)
    self.assertEquals(jl.concretize(value, value), 42)

    value = jl.mkSensitive(x, 41, 20)
    self.assertEquals(jl.concretize(value, value), 20)

  @jeeves
  def test_jif_with_ints(self):
    jl = JeevesLib

    x = jl.mkLabel('x')
    jl.restrict(x, lambda ctxt : ctxt == 42)

    a = 13 if x else 17
    self.assertEquals(jl.concretize(42, a), 13)
    self.assertEquals(jl.concretize(-2, a), 17)

    b = 13 if True else 17
    self.assertEquals(jl.concretize(42, b), 13)
    self.assertEquals(jl.concretize(-2, b), 13)

    c = 13 if False else 17
    self.assertEquals(jl.concretize(42, c), 17)
    self.assertEquals(jl.concretize(-2, c), 17)

    conditional = jl.mkSensitive(x, True, False)
    d = 13 if conditional else 17
    self.assertEquals(jl.concretize(42, d), 13)
    self.assertEquals(jl.concretize(-2, d), 17)

    conditional = jl.mkSensitive(x, False, True)
    d = 13 if conditional else 17
    self.assertEquals(jl.concretize(42, d), 17)
    self.assertEquals(jl.concretize(-2, d), 13)

    y = jl.mkLabel('y')
    z = jl.mkLabel('z')
    jl.restrict(y, lambda (a,_) : a)
    jl.restrict(z, lambda (_,a) : a)
    faceted_int = jl.mkSensitive(y, 10, 0)
    conditional = faceted_int > 5
    i1 = jl.mkSensitive(z, 101, 102)
    i2 = jl.mkSensitive(z, 103, 104)
    f = i1 if conditional else i2
    self.assertEquals(jl.concretize((True, True), f),101)
    self.assertEquals(jl.concretize((True, False), f), 102)
    self.assertEquals(jl.concretize((False, True), f), 103)
    self.assertEquals(jl.concretize((False, False), f), 104)

  @jeeves
  def test_restrict_under_conditional(self):
    x = JeevesLib.mkLabel('x')

    value = JeevesLib.mkSensitive(x, 42, 0)
    if value == 42:
      JeevesLib.restrict(x, lambda ctxt : ctxt == 1)
    self.assertEquals(JeevesLib.concretize(0, value), 0)
    self.assertEquals(JeevesLib.concretize(1, value), 42)

    y = JeevesLib.mkLabel('y')

    value = JeevesLib.mkSensitive(y, 43, 0)
    if value == 42:
        JeevesLib.restrict(y, lambda ctxt : ctxt == 1)
    self.assertEquals(JeevesLib.concretize(0, value), 43)
    self.assertEquals(JeevesLib.concretize(1, value), 43)

  @jeeves
  def test_jbool_functions_fexprs(self):
    jl = JeevesLib

    x = jl.mkLabel('x')
    jl.restrict(x, lambda (a,_) : a == 42)

    for lh in (True, False):
      for ll in (True, False):
        for rh in (True, False):
          for rl in (True, False):
            l = jl.mkSensitive(x, lh, ll)
            r = jl.mkSensitive(x, rh, rl)
            self.assertEquals(jl.concretize((42,0), l and r), lh and rh)
            self.assertEquals(jl.concretize((10,0), l and r), ll and rl)
            self.assertEquals(jl.concretize((42,0), l or r), lh or rh)
            self.assertEquals(jl.concretize((10,0), l or r), ll or rl)
            self.assertEquals(jl.concretize((42,0), not l), not lh)
            self.assertEquals(jl.concretize((10,0), not l), not ll)

    y = jl.mkLabel('y')
    jl.restrict(y, lambda (_,b) : b == 42)

    for lh in (True, False):
      for ll in (True, False):
        for rh in (True, False):
          for rl in (True, False):
            l = jl.mkSensitive(x, lh, ll)
            r = jl.mkSensitive(y, rh, rl)
            self.assertEquals(jl.concretize((42,0), l and r), lh and rl)
            self.assertEquals(jl.concretize((10,0), l and r), ll and rl)
            self.assertEquals(jl.concretize((42,42), l and r), lh and rh)
            self.assertEquals(jl.concretize((10,42), l and r), ll and rh)

            self.assertEquals(jl.concretize((42,0), l or r), lh or rl)
            self.assertEquals(jl.concretize((10,0), l or r), ll or rl)
            self.assertEquals(jl.concretize((42,42), l or r), lh or rh)
            self.assertEquals(jl.concretize((10,42), l or r), ll or rh)
  
  @jeeves
  def test_jif_with_assign(self):
    jl = JeevesLib

    y = jl.mkLabel('y')
    jl.restrict(y, lambda ctxt : ctxt == 42)

    value0 = jl.mkSensitive(y, 0, 1)
    value2 = jl.mkSensitive(y, 2, 3)

    value = value0
    value = value2
    self.assertEquals(jl.concretize(42, value), 2)
    self.assertEquals(jl.concretize(10, value), 3)

    value = 100
    value = value2
    self.assertEquals(jl.concretize(42, value), 2)
    self.assertEquals(jl.concretize(10, value), 3)

    value = value0
    value = 200
    self.assertEquals(jl.concretize(42, value), 200)
    self.assertEquals(jl.concretize(10, value), 200)

    value = 100
    value = 200
    self.assertEquals(jl.concretize(42, value), 200)
    self.assertEquals(jl.concretize(10, value), 200)

  @jeeves
  def test_jif_with_assign_with_pathvars(self):
    jl = JeevesLib

    x = jl.mkLabel('x')
    y = jl.mkLabel('y')
    jl.restrict(x, lambda (a,_) : a)
    jl.restrict(y, lambda (_,b) : b)

    value0 = jl.mkSensitive(y, 0, 1)
    value2 = jl.mkSensitive(y, 2, 3)

    value = value0
    if x:
      value = value2
    self.assertEquals(jl.concretize((True, True), value), 2)
    self.assertEquals(jl.concretize((True, False), value), 3)
    self.assertEquals(jl.concretize((False, True), value), 0)
    self.assertEquals(jl.concretize((False, False), value), 1)

    value = value0
    if not x:
      value = value2
    self.assertEquals(jl.concretize((False, True), value), 2)
    self.assertEquals(jl.concretize((False, False), value), 3)
    self.assertEquals(jl.concretize((True, True), value), 0)
    self.assertEquals(jl.concretize((True, False), value), 1)

  @jeeves
  def test_function_facets(self):
    def add1(a):
        return a+1
    def add2(a):
        return a+2

    jl = JeevesLib

    x = jl.mkLabel('x')
    jl.restrict(x, lambda ctxt : ctxt == 42)

    fun = jl.mkSensitive(x, add1, add2)
    value = fun(15)
    self.assertEquals(jl.concretize(42, value), 16)
    self.assertEquals(jl.concretize(41, value), 17)

  @jeeves
  def test_objects_faceted(self):
    jl = JeevesLib

    x = jl.mkLabel('x')
    jl.restrict(x, lambda ctxt : ctxt)

    y = jl.mkSensitive(x,
      TestClass(1, 2),
      TestClass(3, 4))

    self.assertEquals(jl.concretize(True, y.a), 1)
    self.assertEquals(jl.concretize(True, y.b), 2)
    self.assertEquals(jl.concretize(False, y.a), 3)
    self.assertEquals(jl.concretize(False, y.b), 4)

  @jeeves
  def test_objects_mutate(self):
    jl = JeevesLib

    x = jl.mkLabel('x')
    jl.restrict(x, lambda ctxt : ctxt)

    s = TestClass(1, None)
    t = TestClass(3, None)
    y = jl.mkSensitive(x, s, t)

    if y.a == 1:
      y.a = y.a + 100

    self.assertEquals(jl.concretize(True, y.a), 101)
    self.assertEquals(jl.concretize(True, s.a), 101)
    self.assertEquals(jl.concretize(True, t.a), 3)
    self.assertEquals(jl.concretize(False, y.a), 3)
    self.assertEquals(jl.concretize(False, s.a), 1)
    self.assertEquals(jl.concretize(False, t.a), 3)

  def test_objects_methodcall(self):
    jl = JeevesLib

    x = jl.mkLabel('x')
    jl.restrict(x, lambda ctxt : ctxt)

    s = TestClassMethod(1, 10)
    t = TestClassMethod(100, 1000)
    y = jl.mkSensitive(x, s, t)

    self.assertEquals(jl.concretize(True, y.return_sum()), 11)
    self.assertEquals(jl.concretize(False, y.return_sum()), 1100)

    y.add_a_to_b()
    self.assertEquals(jl.concretize(True, s.a), 1)
    self.assertEquals(jl.concretize(True, s.b), 11)
    self.assertEquals(jl.concretize(True, t.a), 100)
    self.assertEquals(jl.concretize(True, t.b), 1000)
    self.assertEquals(jl.concretize(True, y.a), 1)
    self.assertEquals(jl.concretize(True, y.b), 11)
    self.assertEquals(jl.concretize(False, s.a), 1)
    self.assertEquals(jl.concretize(False, s.b), 10)
    self.assertEquals(jl.concretize(False, t.a), 100)
    self.assertEquals(jl.concretize(False, t.b), 1100)
    self.assertEquals(jl.concretize(False, y.a), 100)
    self.assertEquals(jl.concretize(False, y.b), 1100)