CXX=g++
CXXFLAGS=-std=c++17 -O2 -Wall -Wextra -Iinclude -Ithird_party/nlohmann
TARGET=assignment2_embedding
SRC=src/main.cpp
all: $(TARGET)
$(TARGET): $(SRC) include/types.hpp include/engine.hpp include/embedding.hpp include/experiments.hpp
	$(CXX) $(CXXFLAGS) $(SRC) -o $(TARGET)
clean:
	rm -f $(TARGET) *.o
