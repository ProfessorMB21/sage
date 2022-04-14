r"""
Tensor Algebras

AUTHORS:

- Travis Scrimshaw (2014-01-24): Initial version

.. TODO::

    - Coerce to/from free algebra.
"""

#*****************************************************************************
#  Copyright (C) 2014 Travis Scrimshaw <tscrim at ucdavis.edu>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#                  http://www.gnu.org/licenses/
#*****************************************************************************

from sage.categories.algebras import Algebras
from sage.categories.pushout import ConstructionFunctor
from sage.categories.graded_hopf_algebras_with_basis import GradedHopfAlgebrasWithBasis
from sage.categories.homset import Hom
from sage.categories.morphism import Morphism
from sage.categories.modules import Modules
from sage.categories.tensor import tensor
from sage.combinat.free_module import CombinatorialFreeModule, CombinatorialFreeModule_Tensor
from sage.monoids.indexed_free_monoid import IndexedFreeMonoid
from sage.misc.cachefunc import cached_method
from sage.sets.family import Family

class TensorAlgebra(CombinatorialFreeModule):
    r"""
    The tensor algebra `T(M)` of a module `M`.

    Let `\{ b_i \}_{i \in I}` be a basis of the `R`-module `M`. Then the
    tensor algebra `T(M)` of `M` is an associative `R`-algebra, with a
    basis consisting of all tensors of the form
    `b_{i_1} \otimes b_{i_2} \otimes \cdots \otimes b_{i_n}` for
    nonnegative integers `n` and `n`-tuples
    `(i_1, i_2, \ldots, i_n) \in I^n`. The product of `T(M)` is given by

    .. MATH::

        (b_{i_1} \otimes \cdots \otimes b_{i_m}) \cdot (b_{j_1} \otimes
        \cdots \otimes b_{j_n}) = b_{i_1} \otimes \cdots \otimes b_{i_m}
        \otimes b_{j_1} \otimes \cdots \otimes b_{j_n}.

    As an algebra, it is generated by the basis vectors `b_i` of `M`. It
    is an `\NN`-graded `R`-algebra, with the degree of each `b_i` being
    `1`.

    It also has a Hopf algebra structure: The comultiplication is the
    unique algebra morphism `\delta : T(M) \to T(M) \otimes T(M)` defined
    by:

    .. MATH::

        \delta(b_i) = b_i \otimes 1 + 1 \otimes b_i

    (where the `\otimes` symbol here forms tensors in
    `T(M) \otimes T(M)`, not inside `T(M)` itself). The counit is the
    unique algebra morphism `T(M) \to R` sending each `b_i` to `0`. Its
    antipode `S` satisfies

    .. MATH::

        S(b_{i_1} \otimes \cdots \otimes b_{i_m}) = (-1)^m (b_{i_m} \otimes
        \cdots \otimes b_{i_1}).

    This is a connected graded cocommutative Hopf algebra.

    REFERENCES:

    - :wikipedia:`Tensor_algebra`

    .. SEEALSO::

        :class:`TensorAlgebra`

    EXAMPLES::

        sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
        sage: TA = TensorAlgebra(C)
        sage: TA.dimension()
        +Infinity
        sage: TA.base_ring()
        Rational Field
        sage: TA.algebra_generators()
        Finite family {'a': B['a'], 'b': B['b'], 'c': B['c']}
    """
    def __init__(self, M, prefix='T', category=None, **options):
        r"""
        Initialize ``self``.

        EXAMPLES::

            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: TA = TensorAlgebra(C)
            sage: TestSuite(TA).run()
            sage: m = SymmetricFunctions(QQ).m()
            sage: Tm = TensorAlgebra(m)
            sage: TestSuite(Tm).run()
        """
        self._base_module = M
        R = M.base_ring()
        category = GradedHopfAlgebrasWithBasis(R.category()).or_subcategory(category)

        CombinatorialFreeModule.__init__(self, R, IndexedFreeMonoid(M.indices()),
                                         prefix=prefix, category=category, **options)

        # the following is not the best option, but it's better than nothing.
        self._print_options['tensor_symbol'] = options.get('tensor_symbol', tensor.symbol)

    def _repr_(self):
        r"""
        Return a string representation of ``self``.

        EXAMPLES::

            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: TensorAlgebra(C)
            Tensor Algebra of Free module generated by {'a', 'b', 'c'} over Rational Field
        """
        return "Tensor Algebra of {}".format(self._base_module)

    def _repr_term(self, m):
        """
        Return a string of representation of the term indexed by ``m``.

        TESTS::

            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: TA = TensorAlgebra(C)
            sage: s = TA(['a','b','c']).leading_support()
            sage: TA._repr_term(s)
            "B['a'] # B['b'] # B['c']"
            sage: s = TA(['a']*3 + ['b']*2 + ['a','c','b']).leading_support()
            sage: TA._repr_term(s)
            "B['a'] # B['a'] # B['a'] # B['b'] # B['b'] # B['a'] # B['c'] # B['b']"

            sage: I = TA.indices()
            sage: TA._repr_term(I.one())
            '1'
        """
        if len(m) == 0:
            return '1'
        symb = self._print_options['tensor_symbol']
        if symb is None:
            symb = tensor.symbol
        return symb.join(self._base_module._repr_term(k) for k,e in m._monomial for i in range(e))

    def _latex_term(self, m):
        r"""
        Return a latex representation of the term indexed by ``m``.

        TESTS::

            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: TA = TensorAlgebra(C)
            sage: s = TA(['a','b','c']).leading_support()
            sage: TA._latex_term(s)
            'B_{a} \\otimes B_{b} \\otimes B_{c}'

            sage: I = TA.indices()
            sage: TA._latex_term(I.one())
            '1'
        """
        if len(m) == 0:
            return '1'
        symb = " \\otimes "
        return symb.join(self._base_module._latex_term(k) for k,e in m._monomial for i in range(e))

    def _ascii_art_term(self, m):
        """
        Return an ascii art representation of the term indexed by ``m``.

        TESTS::

            sage: C = CombinatorialFreeModule(QQ, Partitions())
            sage: TA = TensorAlgebra(C)
            sage: s = TA([Partition([3,2,2,1]), Partition([3])]).leading_support()
            sage: TA._ascii_art_term(s)
            B    # B
             ***    ***
             **
             **
             *
            sage: s = TA([Partition([3,2,2,1])]*2 + [Partition([3])]*3 + [Partition([1])]*2).leading_support()
            sage: t = TA._ascii_art_term(s); t
            B    # B    # B    # B    # B    # B  # B
             ***    ***    ***    ***    ***    *    *
             **     **
             **     **
             *      *
            sage: t._breakpoints
            [7, 14, 21, 28, 35, 40]

            sage: I = TA.indices()
            sage: TA._ascii_art_term(I.one())
            '1'
        """
        if len(m) == 0:
            return '1'
        from sage.typeset.ascii_art import AsciiArt, ascii_art
        symb = self._print_options['tensor_symbol']
        if symb is None:
            symb = tensor.symbol
        M = self._base_module
        return ascii_art(*(M._ascii_art_term(k)
                           for k, e in m._monomial for _ in range(e)),
                         sep=AsciiArt([symb], breakpoints=[len(symb)]))

    def _element_constructor_(self, x):
        """
        Construct an element of ``self``.

        EXAMPLES::

            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: TA = TensorAlgebra(C)
            sage: TA(['a','b','c'])
            B['a'] # B['b'] # B['c']
            sage: TA(['a','b','b'])
            B['a'] # B['b'] # B['b']
            sage: TA(['a','b','c']) + TA(['a'])
            B['a'] + B['a'] # B['b'] # B['c']
            sage: TA(['a','b','c']) + TA(['a','b','a'])
            B['a'] # B['b'] # B['a'] + B['a'] # B['b'] # B['c']
            sage: TA(['a','b','c']) + TA(['a','b','c'])
            2*B['a'] # B['b'] # B['c']
            sage: TA(C.an_element())
            2*B['a'] + 2*B['b'] + 3*B['c']
        """
        FM = self._indices
        if isinstance(x, (list, tuple)):
            x = FM.prod(FM.gen(elt) for elt in x)
            return self.monomial(x)
        if x in FM._indices:
            return self.monomial(FM.gen(x))
        if x in self._base_module:
            return self.sum_of_terms((FM.gen(k), v) for k,v in x)
        return CombinatorialFreeModule._element_constructor_(self, x)

    def _tensor_constructor_(self, elts):
        """
        Construct an element of ``self`` that is the tensor product of
        the list of base module elements ``elts``.

        TESTS::

            sage: C = CombinatorialFreeModule(ZZ, ['a','b'])
            sage: TA = TensorAlgebra(C)
            sage: x = C.an_element(); x
            2*B['a'] + 2*B['b']
            sage: TA._tensor_constructor_([x, x])
            4*B['a'] # B['a'] + 4*B['a'] # B['b']
             + 4*B['b'] # B['a'] + 4*B['b'] # B['b']
            sage: y = C.monomial('b') + 3*C.monomial('a')
            sage: TA._tensor_constructor_([x, y])
            6*B['a'] # B['a'] + 2*B['a'] # B['b'] + 6*B['b'] # B['a']
             + 2*B['b'] # B['b']
            sage: TA._tensor_constructor_([y]) == y
            True
            sage: TA._tensor_constructor_([x]) == x
            True
            sage: TA._tensor_constructor_([]) == TA.one()
            True
        """
        if not elts:
            return self.one()

        zero = self.base_ring().zero()
        I = self._indices
        cur = {I.gen(k): v for k,v in elts[0]}
        for x in elts[1:]:
            next = {}
            for k,v in cur.items():
                for m,c in x:
                    i = k * I.gen(m)
                    next[i] = cur.get(i, zero) + v * c
            cur = next
        return self._from_dict(cur)

    def _coerce_map_from_(self, R):
        """
        Return ``True`` if there is a coercion from ``R`` into ``self`` and
        ``False`` otherwise.  The things that coerce into ``self`` are:

        - Anything with a coercion into ``self.base_ring()``.

        - Anything with a coercion into the base module of ``self``.

        - A tensor algebra whose base module has a coercion into the base
          module of ``self``.

        - A tensor module whose factors have a coercion into the base
          module of ``self``.

        TESTS::

            sage: C = CombinatorialFreeModule(ZZ, Set([1,2]))
            sage: TAC = TensorAlgebra(C)
            sage: TAC.has_coerce_map_from(ZZ)
            True
            sage: TAC(1) == TAC.one()
            True
            sage: TAC.has_coerce_map_from(C)
            True
            sage: c = C.monomial(2)
            sage: TAC(c)
            B[2]
            sage: d = C.monomial(1)
            sage: TAC(c) * TAC(d)
            B[2] # B[1]
            sage: TAC(c-d) * TAC(c+d)
            -B[1] # B[1] - B[1] # B[2] + B[2] # B[1] + B[2] # B[2]

            sage: TCC = tensor((C,C))
            sage: TAC.has_coerce_map_from(TCC)
            True
            sage: TAC(tensor([c, d]))
            B[2] # B[1]

        ::

            sage: D = CombinatorialFreeModule(ZZ, Set([2,4]))
            sage: TAD = TensorAlgebra(D)
            sage: f = C.module_morphism(on_basis=lambda x: D.monomial(2*x), codomain=D)
            sage: f.register_as_coercion()

            sage: TCD = tensor((C,D))
            sage: TAD.has_coerce_map_from(TCC)
            True
            sage: TAD.has_coerce_map_from(TCD)
            True
            sage: TAC.has_coerce_map_from(TCD)
            False
            sage: TAD.has_coerce_map_from(TAC)
            True
            sage: TAD(3 * TAC([1, 2, 2, 1, 1]))
            3*B[2] # B[4] # B[4] # B[2] # B[2]
        """
        # Base ring coercions
        self_base_ring = self.base_ring()
        if self_base_ring == R:
            return BaseRingLift(Hom(self_base_ring, self))
        if self_base_ring.has_coerce_map_from(R):
            return BaseRingLift(Hom(self_base_ring, self)) * self_base_ring.coerce_map_from(R)

        M = self._base_module
        # Base module coercions
        if R == M:
            return True
        if M.has_coerce_map_from(R):
            phi = M.coerce_map_from(R)
            return self.coerce_map_from(M) * phi

        # Tensor algebra coercions
        if isinstance(R, TensorAlgebra) and M.has_coerce_map_from(R._base_module):
            RM = R._base_module
            phi = M.coerce_map_from(RM)
            return R.module_morphism(lambda m: self._tensor_constructor_(
                                               [phi(RM.monomial(k)) for k in m.to_word_list()]),
                                     codomain=self)

        # Coercions from tensor products
        if (R in Modules(self_base_ring).WithBasis().TensorProducts()
                and isinstance(R, CombinatorialFreeModule_Tensor)
                and all(M.has_coerce_map_from(RM) for RM in R._sets)):
            modules = R._sets
            vector_map = [M.coerce_map_from(RM) for RM in R._sets]
            return R.module_morphism(lambda x: self._tensor_constructor_(
                                               [vector_map[i](M.monomial(x[i]))
                                                for i,M in enumerate(modules)]),
                                     codomain=self)

        return super(TensorAlgebra, self)._coerce_map_from_(R)

    def construction(self):
        """
        Return the functorial construction of ``self``.

        EXAMPLES::

            sage: C = CombinatorialFreeModule(ZZ, ['a','b','c'])
            sage: TA = TensorAlgebra(C)
            sage: f, M = TA.construction()
            sage: M == C
            True
            sage: f(M) == TA
            True
        """
        return (TensorAlgebraFunctor(self.category().base()), self._base_module)

    def degree_on_basis(self, m):
        """
        Return the degree of the simple tensor ``m``, which is its length
        (thought of as an element in the free monoid).

        EXAMPLES::

            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: TA = TensorAlgebra(C)
            sage: s = TA(['a','b','c']).leading_support(); s
            F['a']*F['b']*F['c']
            sage: TA.degree_on_basis(s)
            3
        """
        return m.length()

    def base_module(self):
        """
        Return the base module of ``self``.

        EXAMPLES::

            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: TA = TensorAlgebra(C)
            sage: TA.base_module() is C
            True
        """
        return self._base_module

    @cached_method
    def one_basis(self):
        r"""
        Return the empty word, which indexes the `1` of this algebra.

        EXAMPLES::

            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: TA = TensorAlgebra(C)
            sage: TA.one_basis()
            1
            sage: TA.one_basis().parent()
            Free monoid indexed by {'a', 'b', 'c'}
            sage: m = SymmetricFunctions(QQ).m()
            sage: Tm = TensorAlgebra(m)
            sage: Tm.one_basis()
            1
            sage: Tm.one_basis().parent()
            Free monoid indexed by Partitions
        """
        return self._indices.one()

    @cached_method
    def algebra_generators(self):
        r"""
        Return the generators of this algebra.

        EXAMPLES::

            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: TA = TensorAlgebra(C)
            sage: TA.algebra_generators()
            Finite family {'a': B['a'], 'b': B['b'], 'c': B['c']}
            sage: m = SymmetricFunctions(QQ).m()
            sage: Tm = TensorAlgebra(m)
            sage: Tm.algebra_generators()
            Lazy family (generator(i))_{i in Partitions}
        """
        return Family(self._indices.indices(),
                      lambda i: self.monomial(self._indices.gen(i)),
                      name='generator')

    gens = algebra_generators

    def product_on_basis(self, a, b):
        r"""
        Return the product of the basis elements indexed by ``a`` and
        ``b``, as per
        :meth:`AlgebrasWithBasis.ParentMethods.product_on_basis()`.

        INPUT:

        - ``a``, ``b`` -- basis indices

        EXAMPLES::

            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: TA = TensorAlgebra(C)
            sage: I = TA.indices()
            sage: g = I.gens()
            sage: TA.product_on_basis(g['a']*g['b'], g['a']*g['c'])
            B['a'] # B['b'] # B['a'] # B['c']
        """
        return self.monomial(a * b)

    def counit(self, x):
        """
        Return the counit of ``x``.

        INPUT:

        - ``x`` -- an element of ``self``

        EXAMPLES::

            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: TA = TensorAlgebra(C)
            sage: x = TA(['a','b','c'])
            sage: TA.counit(x)
            0
            sage: TA.counit(x + 3)
            3
        """
        return x[self.one_basis()]

    def antipode_on_basis(self, m):
        """
        Return the antipode of the simple tensor indexed by ``m``.

        EXAMPLES::

            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: TA = TensorAlgebra(C)
            sage: s = TA(['a','b','c']).leading_support()
            sage: TA.antipode_on_basis(s)
            -B['c'] # B['b'] # B['a']
            sage: t = TA(['a', 'b', 'b', 'b']).leading_support()
            sage: TA.antipode_on_basis(t)
            B['b'] # B['b'] # B['b'] # B['a']
        """
        m = self._indices(reversed(m._monomial))
        R = self.base_ring()
        if len(m) % 2 == 1:
            return self.term(m, -R.one())
        else:
            return self.term(m, R.one())

    def coproduct_on_basis(self, m):
        r"""
        Return the coproduct of the simple tensor indexed by ``m``.

        EXAMPLES::

            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: TA = TensorAlgebra(C, tensor_symbol="(X)")
            sage: TA.coproduct_on_basis(TA.one_basis())
            1 # 1
            sage: I = TA.indices()
            sage: ca = TA.coproduct_on_basis(I.gen('a')); ca
            1 # B['a'] + B['a'] # 1
            sage: s = TA(['a','b','c']).leading_support()
            sage: cp = TA.coproduct_on_basis(s); cp
            1 # B['a'](X)B['b'](X)B['c'] + B['a'] # B['b'](X)B['c']
             + B['a'](X)B['b'] # B['c'] + B['a'](X)B['b'](X)B['c'] # 1
             + B['a'](X)B['c'] # B['b'] + B['b'] # B['a'](X)B['c']
             + B['b'](X)B['c'] # B['a'] + B['c'] # B['a'](X)B['b']

        We check that `\Delta(a \otimes b \otimes c) =
        \Delta(a) \Delta(b) \Delta(c)`::

            sage: cb = TA.coproduct_on_basis(I.gen('b'))
            sage: cc = TA.coproduct_on_basis(I.gen('c'))
            sage: cp == ca * cb * cc
            True
        """
        S = self.tensor_square()
        if len(m) == 0:
            return S.one()

        if len(m) == 1:
            ob = self.one_basis()
            return S.sum_of_monomials([(m, ob), (ob, m)])

        I = self._indices
        m_word = [k for k,e in m._monomial for dummy in range(e)]
        ob = self.one_basis()
        return S.prod(S.sum_of_monomials([(I.gen(x), ob), (ob, I.gen(x))])
                      for x in m_word)

        # TODO: Implement a coproduct using shuffles.
        # This isn't quite right:
        #from sage.combinat.words.word import Word
        #k = len(m)
        #return S.sum_of_monomials( (I.prod(I.gen(m_word[i]) for i in w[:p]),
        #                            I.prod(I.gen(m_word[i]) for i in w[p:]))
        #                          for p in range(k+1)
        #                          for w in Word(range(p)).shuffle(range(p, k)) )

#####################################################################
## TensorAlgebra functor

class TensorAlgebraFunctor(ConstructionFunctor):
    r"""
    The tensor algebra functor.

    Let `R` be a unital ring. Let `V_R` and `A_R` be the categories of
    `R`-modules and `R`-algebras respectively. The functor
    `T : V_R \to A_R` sends an `R`-module `M` to the tensor
    algebra `T(M)`. The functor `T` is left-adjoint to the forgetful
    functor `F : A_R \to V_R`.

    INPUT:

    - ``base`` -- the base `R`
    """
    # We choose a larger (functor) rank than most ConstructionFunctors
    #   since this should be applied after all of the module functors
    rank = 20

    def __init__(self, base):
        """
        Initialize ``self``.

        EXAMPLES::

            sage: from sage.algebras.tensor_algebra import TensorAlgebraFunctor
            sage: F = TensorAlgebraFunctor(Rings())
            sage: TestSuite(F).run()
        """
        ConstructionFunctor.__init__(self, Modules(base), Algebras(base))

    def _repr_(self):
        """
        Return a string representation of ``self``.

        EXAMPLES::

            sage: from sage.algebras.tensor_algebra import TensorAlgebraFunctor
            sage: TensorAlgebraFunctor(Rings())
            Tensor algebra functor on modules over rings
            sage: TensorAlgebraFunctor(QQ)
            Tensor algebra functor on vector spaces over Rational Field
        """
        return "Tensor algebra functor on {}".format(self.domain()._repr_object_names())

    def _apply_functor(self, M):
        """
        Construct the tensor algebra `T(M)`.

        EXAMPLES::

            sage: from sage.algebras.tensor_algebra import TensorAlgebraFunctor
            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: F = TensorAlgebraFunctor(QQ)
            sage: F._apply_functor(C)
            Tensor Algebra of Free module generated by {'a', 'b', 'c'} over Rational Field
        """
        if M not in self.domain().WithBasis():
            raise NotImplementedError("currently only for modules with basis")
        return TensorAlgebra(M)

    def _apply_functor_to_morphism(self, f):
        """
        Apply ``self`` to a morphism ``f`` in the domain of ``self``.

        EXAMPLES::

            sage: from sage.algebras.tensor_algebra import TensorAlgebraFunctor
            sage: C = CombinatorialFreeModule(QQ, ['a','b','c'])
            sage: D = CombinatorialFreeModule(QQ, ['x','y'])
            sage: on_basis = lambda m: C.term('a', 2) + C.monomial('b') if m == 'x' else sum(C.basis())
            sage: phi = D.module_morphism(on_basis, codomain=C); phi
            Generic morphism:
              From: Free module generated by {'x', 'y'} over Rational Field
              To:   Free module generated by {'a', 'b', 'c'} over Rational Field
            sage: list(map(phi, D.basis()))
            [2*B['a'] + B['b'], B['a'] + B['b'] + B['c']]
            sage: F = TensorAlgebraFunctor(QQ)
            sage: Tphi = F._apply_functor_to_morphism(phi); Tphi
            Generic morphism:
              From: Tensor Algebra of Free module generated by {'x', 'y'} over Rational Field
              To:   Tensor Algebra of Free module generated by {'a', 'b', 'c'} over Rational Field
            sage: G = F(D).algebra_generators()
            sage: list(map(Tphi, G))
            [2*B['a'] + B['b'], B['a'] + B['b'] + B['c']]
            sage: Tphi(sum(G))
            3*B['a'] + 2*B['b'] + B['c']
            sage: Tphi(G['x'] * G['y'])
            2*B['a'] # B['a'] + 2*B['a'] # B['b'] + 2*B['a'] # B['c']
             + B['b'] # B['a'] + B['b'] # B['b'] + B['b'] # B['c']
        """
        DB = f.domain()
        D = self(DB)
        C = self(f.codomain())
        phi = lambda m: C._tensor_constructor_([f(DB.monomial(k))
                                                for k in m.to_word_list()])
        return D.module_morphism(phi, codomain=C)

#####################################################################
## Lift map from the base ring

class BaseRingLift(Morphism):
    r"""
    Morphism `R \to T(M)` which identifies the base ring `R` of a tensor
    algebra `T(M)` with the `0`-th graded part of `T(M)`.
    """
    def _call_(self, x):
        """
        Construct the image of ``x``.

        TESTS::

            sage: C = CombinatorialFreeModule(QQ, Set([1,2]))
            sage: TA = TensorAlgebra(C)
            sage: TA(ZZ(2))
            2
        """
        T = self.codomain()
        R = T.base_ring()
        return T.term(T.indices().one(), R(x))
