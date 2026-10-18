#pragma once
// Vector arithmetic on std::vector<double>. Pure math, no domain knowledge.
// Ported from the parent project's vector_space with the additions the evaluation needs
// (l2Norm alias, mean, variance, hadamard, slice, cosine over arbitrary ranges).
#include <cstddef>
#include <string>
#include <vector>

namespace careweave {
namespace embedding {

using Vector = std::vector<double>;

struct VectorMath {
  static double dot(const Vector& a, const Vector& b);
  static double norm(const Vector& a);
  static double euclideanDistance(const Vector& a, const Vector& b);
  // Cosine similarity. Returns 0.0 when either vector has zero norm, never NaN.
  static double cosine(const Vector& a, const Vector& b);
  // Cosine restricted to [begin, end) of both vectors.
  static double cosineRange(const Vector& a, const Vector& b, size_t begin, size_t end);
  static Vector add(const Vector& a, const Vector& b);
  static Vector subtract(const Vector& a, const Vector& b);
  static Vector scale(const Vector& a, double s);
  static Vector hadamard(const Vector& a, const Vector& b);
  static Vector normalize(const Vector& a);
  static Vector concat(const Vector& a, const Vector& b);
  static Vector slice(const Vector& a, size_t begin, size_t end);
  static Vector mean(const std::vector<Vector>& vectors);   // zero vector when empty
  static double meanValue(const Vector& a);
  static double variance(const Vector& a);
  static size_t argMax(const Vector& a);
  static std::string toString(const Vector& v, int maxElems = 8);
};

}  // namespace embedding
}  // namespace careweave
