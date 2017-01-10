// Algorithms for indefinite and definite summation
//
// (c) 2016  Ralf Stephan <ralf@ark.in-berlin.de>
// Distributed under GPL2, see http://www.gnu.org
//
// Ref.:       1. W. Koepf, Algorithms for m-fold Hypergeometric Summation,
//                  Journal of Symbolic Computation (1995) 20, 399-417

#include <stdexcept>
#include <unordered_map>
#include <unordered_set>

#include "inifcns.h"
#include "ex.h"
#include "mul.h"
#include "add.h"
#include "numeric.h"
#include "function.h"
#include "symbol.h"
#include "utils.h"
#include "operators.h"
#include "relational.h"
#include "normal.h"
#include "upoly.h"
#include "mpoly.h"
#include "matrix.h"

namespace GiNaC {

class gosper_domain_error : public std::domain_error {
        public:
                gosper_domain_error() : std::domain_error("") {}
};

static bool is_rational_linear(const ex& the_ex)
{
        if (is_exactly_a<symbol>(the_ex))
                return true;
        if (is_exactly_a<numeric>(the_ex))
                return (ex_to<numeric>(the_ex).is_mpz()
                                or ex_to<numeric>(the_ex).is_mpq());

        if (is_exactly_a<mul>(the_ex)) {
                const mul& m = ex_to<mul>(the_ex);
                for (unsigned int i=0; i<m.nops(); i++) {
                        if (not is_exactly_a<symbol>(m.op(i))
                            and not is_exactly_a<numeric>(m.op(i)))
                                return false;
                }
                const ex& oc = m.op(m.nops());
                return (is_exactly_a<numeric>(oc)
                       and (ex_to<numeric>(oc).is_mpz()
                            or ex_to<numeric>(oc).is_mpq()));
        }
        if (is_exactly_a<add>(the_ex)) {
                const add& a = ex_to<add>(the_ex);
                for (unsigned int i=0; i<a.nops(); i++) {
                        if (not is_rational_linear(a.op(i)))
                                return false;
                }
                const ex& oc = a.op(a.nops());
                return (is_exactly_a<numeric>(oc)
                       and (ex_to<numeric>(oc).is_mpz()
                            or ex_to<numeric>(oc).is_mpq()));
        }
        return false;
}

static ex factorial_to_gamma(const function& f)
{
        return tgamma(f.op(0) + _ex1);
}

static ex gamma_to_gamma(const function& f) { return ex(f); }

static ex binomial_to_gamma(const function& f)
{
        const ex& a = f.op(0);
        const ex& k = f.op(1);
        if (is_exactly_a<numeric>(a)) {
                numeric anum = ex_to<numeric>(a);
                if (anum.info(info_flags::integer)
                    and anum.info(info_flags::negative))
                        return pow(_ex_1, k) * 
                                (tgamma(k - a) / (tgamma(k+1) * (anum-*_num1_p).factorial()));
        }
        ex t = (k - a).expand();
        if (is_exactly_a<numeric>(t)
            and ex_to<numeric>(t).info(info_flags::integer)
            and ex_to<numeric>(t).info(info_flags::negative))
                return _ex0;

        return tgamma(a+1) / (tgamma(k+1) * tgamma(a-k+1));
}

static ex rising_factorial_to_gamma(const function& f)
{
        return tgamma(f.op(0) + f.op(1)) / tgamma(f.op(0));
}

static ex falling_factorial_to_gamma(const function& f)
{
        return tgamma(f.op(0) + _ex1) / tgamma(f.op(0) - f.op(1) + _ex_1);
}

using tgfun_t = decltype(gamma_to_gamma);
static std::unordered_map<unsigned int,tgfun_t*> funcmap {{
        {factorial_SERIAL::serial, &factorial_to_gamma},
        {tgamma_SERIAL::serial, &gamma_to_gamma},
        {binomial_SERIAL::serial, &binomial_to_gamma},
        {rising_factorial_SERIAL::serial, &rising_factorial_to_gamma},
        {falling_factorial_SERIAL::serial, &falling_factorial_to_gamma},
}};

static bool has_suitable_form(ex the_ex)
{
        if (is_rational_linear(the_ex))
                return true;
        if (is_exactly_a<power>(the_ex)) {
                power pow = ex_to<power>(the_ex);
                const ex& expo = pow.op(1);
                if (is_exactly_a<numeric>(expo)
                    and expo.info(info_flags::integer))
                        return has_suitable_form(pow.op(0));
                return (is_rational_linear(pow.op(0))
                     and is_rational_linear(pow.op(1)));
        }
        if (is_exactly_a<function>(the_ex)) {
                function f = ex_to<function>(the_ex);
                if (funcmap.find(f.get_serial()) == funcmap.end())
                        return false;
                for (unsigned int i=0; i<f.nops(); i++)
                        if (not is_rational_linear(f.op(i)))
                                return false;
                return true;
        }
        if (is_exactly_a<mul>(the_ex)) {
                const mul& m = ex_to<mul>(the_ex);
                for (unsigned int i=0; i<m.nops(); i++) {
                        if (not has_suitable_form(m.op(i)))
                                return false;
                }
                const ex& oc = m.op(m.nops());
                return (is_exactly_a<numeric>(oc)
                       and (ex_to<numeric>(oc).is_mpz()
                            or ex_to<numeric>(oc).is_mpq()));
        }
        if (is_exactly_a<add>(the_ex)) {
                const add& m = ex_to<add>(the_ex);
                for (unsigned int i=0; i<m.nops(); i++) {
                        if (not has_suitable_form(m.op(i)))
                                return false;
                }
                const ex& oc = m.op(m.nops());
                return (is_exactly_a<numeric>(oc)
                       and (ex_to<numeric>(oc).is_mpz()
                            or ex_to<numeric>(oc).is_mpq()));
        }
        return false;
}

ex to_gamma(const ex& the_ex)
{
        if (is_rational_linear(the_ex))
                return the_ex;
        if (is_exactly_a<power>(the_ex)) {
                power pow = ex_to<power>(the_ex);
                const ex& expo = pow.op(1);
                if (is_exactly_a<numeric>(expo)
                    and expo.info(info_flags::integer))
                        return power(to_gamma(pow.op(0)), expo);
                return the_ex;
        }
        if (is_exactly_a<function>(the_ex)) {
                function f = ex_to<function>(the_ex);
                auto search = funcmap.find(f.get_serial());
                if (search == funcmap.end())
                        return the_ex;
                return (*search->second)(f);
        }
        if (is_exactly_a<mul>(the_ex)) {
                const mul& m = ex_to<mul>(the_ex);
                exvector vec;
                for (unsigned int i=0; i<m.nops(); i++)
                        vec.push_back(to_gamma(m.op(i)));
                return mul(vec);
        }
        if (is_exactly_a<add>(the_ex)) {
                const add& m = ex_to<add>(the_ex);
                exvector vec;
                for (unsigned int i=0; i<m.nops(); i++)
                        vec.push_back(to_gamma(m.op(i)));
                return add(vec);
        }
        throw std::runtime_error("can't happen in to_gamma");
}

static ex combine_powers(const ex& the_ex)
{
        if (not is_exactly_a<mul>(the_ex))
                return the_ex;

        // The main data struct holds gamma arguments and their exponents
        exmap factors;
        const mul& m = ex_to<mul>(the_ex);
        ex res = _ex1;
        for (unsigned int i=0; i<m.nops(); i++) {
                const ex& term = m.op(i);
                if (is_exactly_a<function>(term)) {
                        res = res * term;
                        continue;
                }
                if (is_exactly_a<power>(term)) {
                        const power& p = ex_to<power>(term);
                        ex basis = p.op(0);
                        ex expo = p.op(1);
                        if (is_exactly_a<numeric>(expo)
                            and is_exactly_a<power>(basis)
                            and ex_to<numeric>(expo) == *_num_1_p) {
                                const power& bbasis = ex_to<power>(basis);
                                expo = bbasis.op(1) * _ex_1;
                                basis = bbasis.op(0);
                        }
                        auto search = factors.find(basis);
                        if (search == factors.end())
                                factors[basis] = expo;
                        else
                                search->second += expo;
                }
                else {
                        auto search = factors.find(term);
                        if (search == factors.end())
                                factors[term] = _ex1;
                        else
                                search->second += _ex1;
                }
        }

        for (auto& f : factors)
                res *= power(f.first, f.second);
        return res;
}

using ex_intset_map = std::map<GiNaC::ex, std::unordered_set<int>, GiNaC::ex_is_less>;
static void collect_gamma_args(ex the_ex, ex_intset_map& map)
{
        if (is_exactly_a<function>(the_ex)) {
                function f = ex_to<function>(the_ex);
                if (f.get_serial() == tgamma_SERIAL::serial) {
                        ex arg = f.op(0).expand();
                        if (is_exactly_a<numeric>(arg))
                                return;
                        ex oc;
                        if (is_exactly_a<add>(arg)) {
                                const add& a = ex_to<add>(arg);
                                oc = a.op(a.nops());
                                if (not is_exactly_a<numeric>(oc))
                                        return;
                                numeric noc = ex_to<numeric>(oc);
                                if (not noc.is_mpz()) {
                                        if (not noc.is_mpq())
                                                return;
                                        oc = numeric(noc.to_int());
                                }
                        }
                        else
                                oc = _ex0;
                        int ioc = ex_to<numeric>(oc).to_int();
                        auto search = map.find(arg - oc);
                        if (search != map.end()) {
                                search->second.insert(ioc);
                        }
                        else {
                                std::unordered_set<int> intset;
                                intset.insert(ioc);
                                map[arg-oc] = intset;
                        }
                }
                for (unsigned int i=0; i<f.nops(); i++)
                        collect_gamma_args(f.op(i), map);
        }
        else if (is_exactly_a<power>(the_ex)) {
                power pow = ex_to<power>(the_ex);
                collect_gamma_args(pow.op(0), map);
                collect_gamma_args(pow.op(1), map);
        }
        else if (is_a<expairseq>(the_ex)) {
                const expairseq& epseq = ex_to<expairseq>(the_ex);
                for (unsigned int i=0; i<epseq.nops(); i++)
                        collect_gamma_args(epseq.op(i), map);
        }
}

ex gamma_normalize(ex the_ex)
{
        ex_intset_map map;
        collect_gamma_args(the_ex, map);
        exmap submap;
        for (const auto& p : map) {
                if (p.second.size() < 2)
                        continue;
                int m = *std::min_element(p.second.begin(), p.second.end());
                for (int oc : p.second) {
                        if (oc == m)
                                continue;
                        ex prod = _ex1;
                        const ex& base = p.first;
                        for (int i=m; i<oc; ++i)
                                prod *= (base + numeric(i));
                        submap[tgamma(base + numeric(oc)).hold()] = tgamma(base + numeric(m)).hold() * prod;
                }
        }

        ex subsed = the_ex.subs(submap).normal(0, true, false);
        ex res_ex;
        bool res = factor(subsed, res_ex);
        if (res)
                return res_ex;
        else
                return subsed;
}

ex hypersimp(const ex& e, const ex& k)
// See Algorithm 2.1 in the Koepf reference
{
        ex f = e.expand();
        ex g = (f.subs(k == k-_ex_1)) / f;
        ex gf;
        bool red = factor(g, gf);
        ex& gr = gf;
        if (not red)
                gr = g;
        if (not has_suitable_form(gr))
                throw gosper_domain_error();

        return combine_powers(gamma_normalize(to_gamma(gr)));
}

static ex diagonal_poly(const exvector& syms, const ex& var)
// Return sum(0<=i<n, sym_i * var^i)
{
        unsigned int n = syms.size();
        ex res = _ex0;
        for (unsigned int i=0; i<n; ++i)
                res += power(var, i) * syms[n-i-1];
        return res;
}

static ex binomial_poly(const exvector& syms, const ex& var)
// Return sum(0<=i<n, sym_i * (var+1)^i) already expanded
{
        unsigned int n = syms.size();
        ex res = _ex0;
        for (unsigned int row=0; row<n; ++row) {
                const ex& v = power(var, row);
                for (unsigned int col=0; col<n; ++col) {
                        if (row+col < n)
                                res += v * binomial(row+col, col) * syms[n-col-row-1];
                }
        }
        return res;
}

static matrix solve_system(ex mpoly,
                const exvector& syms, const ex& msym)
// Solve mpoly==0 by converting to a linear system
{
        mpoly = mpoly.expand();
        if (not is_exactly_a<add>(mpoly))
                throw gosper_domain_error();
        ex_int_map sym_idx;
        const size_t nc = syms.size(), nr = mpoly.degree(msym) + 1;
        for (size_t i=0; i<nc; ++i)
                sym_idx[syms[i]] = i;
        exmap zero_syms;
        for (const auto& sym : syms)
                zero_syms[sym] = _ex0;
        matrix mat(nr, nc), vars(nc, 1), rhs(nr, 1);
        expairvec coeffs;
        mpoly.coefficients(msym, coeffs);
        for (const auto& pair : coeffs) {
                const ex& term = pair.first;
                const ex& expo = pair.second;
                if (not is_exactly_a<numeric>(expo))
                        throw std::runtime_error("can't happen in solve_system()");
                numeric nume = ex_to<numeric>(expo);
                if (not nume.is_mpz())
                        throw std::runtime_error("can't happen in solve_system()");
                int e = nume.to_int();
                for (const ex& sym : syms) {
                        auto search = sym_idx.find(sym);
                        if (search == sym_idx.end())
                                throw std::runtime_error("unknown symbol in solve_system()");
                        ex coeff = term.coeff(sym);
                        int s = search->second;
                        mat(e, s) = coeff;
                }
                rhs(e, 0) = -(term.subs(zero_syms));
        }
        for (size_t i=0; i<nc; ++i)
                vars(i, 0) = syms[i];
        matrix res = mat.solve(vars, rhs, solve_algo::automatic);
        return res;
}

static std::set<int> nonneg_integer_roots(const ex& poly, const symbol& v)
{
        std::set<int> roots;
        roots.insert(1);
        symbolset s = poly.symbols();
        if (s.size() > 1)
                return roots;
        numeric lcm = lcm_of_coefficients_denominators(poly);
        ex p = multiply_lcm(poly, lcm);
        p = p.primpart(v);
        int ldeg = p.ldegree(v);
        if (ldeg > 0)
                roots.insert(0);
        numeric c = ex_to<numeric>(p.coeff(v, ldeg));
        if (not c.is_integer())
                throw std::runtime_error("can't happen in nonneg_integer_roots");
        c.divisors(roots);
        for (auto it = roots.begin(); it != roots.end(); )
                if (not poly.subs(v == numeric(*it)).is_zero())
                        it = roots.erase(it);
                else
                        ++it;
        return std::move(roots);
}

ex gosper_term(ex e, ex n)
{
        ex the_ex = hypersimp(e, n);
        ex num = the_ex.numer().expand();
        ex den = the_ex.denom().expand();
        ex cn = num.lcoeff(n);
        ex cd = den.lcoeff(n);
        ex ldq = (cn / cd).normal(0, true, false);
        ex A = (num / cn).normal(0, true, false);
        ex B = (den / cd).normal(0, true, false);
        ex C = _ex1;
        symbol h;
        ex res;
        try {
                res = resultant(A, B.subs(n == n+h), n);
        }
        catch (std::runtime_error) {
                throw std::runtime_error("NotImplemented: we cannot solve that at the moment");
        }
        std::set<int> roots = nonneg_integer_roots(res, h);
        for (int root : roots) {
                ex d = gcd(A, B.subs(n == n+ex(root)).expand());
                A = quo(A, d, n, false);
                B = quo(B, d.subs(n == n-ex(root)), false);
                for (long j=1; j<root+1; ++j)
                        C *= d.subs(n == n-ex(j));
        }
        A = (A * ldq).normal(0, true, false);
        B = B.subs(n == n-1).expand();
        int N = A.degree(n);
        int M = B.degree(n);
        int K = C.degree(n);
        std::unordered_set<int> D;
        if (N != M or not A.lcoeff(n).is_equal(B.lcoeff(n)))
                D.insert(K - std::max(M,N));
        else if (N == 0) {
                D.insert(K - N + 1);
                D.insert(0);
        }
        else {
                D.insert(K - N + 1);
                ex t = (B.coeff(n,N-1) - A.coeff(n,N-1)) / A.lcoeff(n);
                if (is_exactly_a<numeric>(t)
                    and ex_to<numeric>(t).info(info_flags::integer)
                    and ex_to<numeric>(t) >= *_num0_p)
                                D.insert(ex_to<numeric>(t).to_int());
        }
        if (D.empty())
                throw gosper_domain_error();
        int d = *std::max_element(D.begin(), D.end());
        exvector syms;
        for (int i=0; i<d+1; ++i)
                syms.push_back((new symbol)->setflag(status_flags::dynallocated));
        ex xshifted = binomial_poly(syms, n);
        ex x = diagonal_poly(syms, n);
        ex H = A*xshifted - B*x -C;
        auto solution = solve_system(H, syms, n);
        for (size_t i=0; i<solution.rows(); ++i) {
                ex sym = syms[i];
                ex val = ex_to<numeric>(solution(i,0));
                x = x.subs(sym == val);
        }
        for (size_t i=0; i<syms.size(); ++i) {
                ex sym = syms[i];
                x = x.subs(sym == _ex0);
        }
        return B*x / C;
}

ex gosper_sum_definite(ex f, ex s, ex a, ex b, int* success)
{
        try {
                ex g = gosper_term(f, s);
                ex t = (f*(g + _ex1)).subs(s==b) - (f*g).expand().subs(s==a);
                *success = 1;
                ex res;
                bool changed = factor(t, res);
                if (changed)
                        return res;
                else
                        return t;
        }
        catch (gosper_domain_error) {
                *success = 0;
                return _ex0;
        }
}

ex gosper_sum_indefinite(ex f, ex s, int* success)
{
        try {
                ex t = f*gosper_term(f, s);
                *success = 1;
                ex res;
                bool changed = factor(t, res);
                if (changed)
                        return res;
                else
                        return t;
        }
        catch (gosper_domain_error) {
                *success = 0;
                return _ex0;
        }
}

}
