#ifndef SIMILARITY_H
#define SIMILARITY_H

#include "types.h"

class Similarity
{
public:
    static double cosine(
        const FeatureVector& a,
        const FeatureVector& b
    );
};

#endif