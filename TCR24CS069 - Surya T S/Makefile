CXX ?= g++
CXXFLAGS = -std=c++14 -Wall -Wextra -O2 -Iinclude -Ithird_party

TARGET = capability_embedding
TEST_TARGET = test_embedding

SRCS = src/main.cpp
TEST_SRCS = tests/test_embedding.cpp

all: $(TARGET) $(TEST_TARGET)

$(TARGET): $(SRCS) include/types.hpp include/embedding.hpp include/json_loader.hpp include/experiments.hpp
	$(CXX) $(CXXFLAGS) $(SRCS) -o $(TARGET)

$(TEST_TARGET): $(TEST_SRCS) include/types.hpp include/embedding.hpp include/json_loader.hpp
	$(CXX) $(CXXFLAGS) $(TEST_SRCS) -o $(TEST_TARGET)

test: $(TEST_TARGET)
	./$(TEST_TARGET)

run: $(TARGET)
	./$(TARGET) --all

ifeq ($(OS),Windows_NT)
    CLEAN_CMD = cmd /c "del /f /q $(TARGET) $(TARGET).exe $(TEST_TARGET) $(TEST_TARGET).exe 2>nul"
else
    CLEAN_CMD = rm -f $(TARGET) $(TARGET).exe $(TEST_TARGET) $(TEST_TARGET).exe
endif

clean:
	-$(CLEAN_CMD)

.PHONY: all test run clean
