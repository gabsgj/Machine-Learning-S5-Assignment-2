#include "careweave/embedding/vector.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>

namespace careweave {
namespace embedding {

double VectorMath::dot(const Vector& a, const Vector& b) {
  const size_t n = std::min(a.size(), b.size());
  double s = 0.0;
  for (size_t i = 0; i < n; ++i) s += a[i] * b[i];
  return s;
}

double VectorMath::norm(const Vector& a) { return std::sqrt(dot(a, a)); }

double VectorMath::euclideanDistance(const Vector& a, const Vector& b) {
  const size_t n = std::max(a.size(), b.size());
  double s = 0.0;
  for (size_t i = 0; i < n; ++i) {
    const double x = i < a.size() ? a[i] : 0.0;
    const double y = i < b.size() ? b[i] : 0.0;
    const double d = x - y;
    s += d * d;
  }
  return std::sqrt(s);
}

double VectorMath::cosine(const Vector& a, const Vector& b) {
  const double na = norm(a);
  const double nb = norm(b);
  if (na <= 0.0 || nb <= 0.0) return 0.0;
  return dot(a, b) / (na * nb);
}

double VectorMath::cosineRange(const Vector& a, const Vector& b, size_t begin, size_t end) {
  if (end > a.size()) end = a.size();
  if (end > b.size()) end = std::min(end, b.size());
  if (begin >= end) return 0.0;
  double d = 0.0, na = 0.0, nb = 0.0;
  for (size_t i = begin; i < end; ++i) {
    d += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  if (na <= 0.0 || nb <= 0.0) return 0.0;
  return d / (std::sqrt(na) * std::sqrt(nb));
}

Vector VectorMath::add(const Vector& a, const Vector& b) {
  const size_t n = std::max(a.size(), b.size());
  Vector r(n, 0.0);
  for (size_t i = 0; i < n; ++i) {
    if (i < a.size()) r[i] += a[i];
    if (i < b.size()) r[i] += b[i];
  }
  return r;
}

Vector VectorMath::subtract(const Vector& a, const Vector& b) {
  const size_t n = std::max(a.size(), b.size());
  Vector r(n, 0.0);
  for (size_t i = 0; i < n; ++i) {
    if (i < a.size()) r[i] += a[i];
    if (i < b.size()) r[i] -= b[i];
  }
  return r;
}

Vector VectorMath::scale(const Vector& a, double s) {
  Vector r = a;
  for (auto& x : r) x *= s;
  return r;
}

Vector VectorMath::hadamard(const Vector& a, const Vector& b) {
  const size_t n = std::max(a.size(), b.size());
  Vector r(n, 0.0);
  for (size_t i = 0; i < n; ++i) {
    const double x = i < a.size() ? a[i] : 0.0;
    const double y = i < b.size() ? b[i] : 0.0;
    r[i] = x * y;
  }
  return r;
}

Vector VectorMath::normalize(const Vector& a) {
  const double n = norm(a);
  if (n <= 0.0) return a;
  return scale(a, 1.0 / n);
}

Vector VectorMath::concat(const Vector& a, const Vector& b) {
  Vector r = a;
  r.insert(r.end(), b.begin(), b.end());
  return r;
}

Vector VectorMath::slice(const Vector& a, size_t begin, size_t end) {
  if (begin >= a.size()) return Vector();
  end = std::min(end, a.size());
  return Vector(a.begin() + static_cast<long>(begin), a.begin() + static_cast<long>(end));
}

Vector VectorMath::mean(const std::vector<Vector>& vectors) {
  if (vectors.empty()) return Vector();
  size_t n = 0;
  for (const auto& v : vectors) n = std::max(n, v.size());
  Vector r(n, 0.0);
  for (const auto& v : vectors) {
    for (size_t i = 0; i < v.size(); ++i) r[i] += v[i];
  }
  const double k = 1.0 / static_cast<double>(vectors.size());
  for (auto& x : r) x *= k;
  return r;
}

double VectorMath::meanValue(const Vector& a) {
  if (a.empty()) return 0.0;
  double s = 0.0;
  for (double x : a) s += x;
  return s / static_cast<double>(a.size());
}

double VectorMath::variance(const Vector& a) {
  if (a.empty()) return 0.0;
  const double m = meanValue(a);
  double s = 0.0;
  for (double x : a) s += (x - m) * (x - m);
  return s / static_cast<double>(a.size());
}

size_t VectorMath::argMax(const Vector& a) {
  size_t best = 0;
  for (size_t i = 1; i < a.size(); ++i) {
    if (a[i] > a[best]) best = i;
  }
  return best;
}

std::string VectorMath::toString(const Vector& v, int maxElems) {
  std::ostringstream os;
  os << "[";
  for (size_t i = 0; i < v.size() && i < static_cast<size_t>(maxElems); ++i) {
    if (i) os << ",";
    os << v[i];
  }
  if (v.size() > static_cast<size_t>(maxElems)) os << ",...";
  os << "](" << v.size() << ")";
  return os.str();
}

}  // namespace embedding
}  // namespace careweave
