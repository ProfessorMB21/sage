from sage.libs.mpfr.types cimport mpfr_rnd_t, mpfr_t

cimport sage.rings.ring
cimport sage.rings.abc
cimport sage.structure.element
from cypari2.types cimport GEN
from sage.libs.mpfr.types cimport mpfr_prec_t

cdef class RealNumber(sage.structure.element.RingElement)  # forward decl

cdef class RealField_class(sage.rings.abc.RealField):
    cdef mpfr_prec_t _prec
    cdef bint sci_not
    cdef mpfr_rnd_t rnd
    cdef object rnd_str
    cdef inline RealNumber _new(self) noexcept:
        """Return a new real number with parent ``self``."""
        return <RealNumber>(RealNumber.__new__(RealNumber, self))

cdef class RealNumber(sage.structure.element.RingElement):
    cdef mpfr_t value
    cdef inline RealNumber _new(self) noexcept:
        """Return a new real number with same parent as ``self``."""
        return <RealNumber>(RealNumber.__new__(RealNumber, self._parent))
    cpdef _add_(self, other) noexcept
    cpdef _mul_(self, other) noexcept
    cpdef _mod_(self, right) noexcept
    cdef _set(self, x, int base) noexcept
    cdef _set_from_GEN_REAL(self, GEN g) noexcept
    cdef RealNumber abs(RealNumber self) noexcept

cpdef RealField(mpfr_prec_t prec=*, int sci_not=*, rnd=*) noexcept
