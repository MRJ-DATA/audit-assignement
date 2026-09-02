import importlib.util
import sys

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# a deterministic fake "encoder" -- doesn't matter that it's not real GPT-2,
# what matters is it's the SAME function used against BOTH script versions
def fake_encode(s):
    return list(s.encode("utf-8"))  # one "token" per UTF-8 byte, deterministic

orig = load_module("fertility_original.py", "orig")
no_rand = load_module("fertility_no_random.py", "no_rand")

test_lines = [
    "The train arrived exactly on time.",
    "Bengaluru International Airport handled record traffic in March.",
    "मुझे सुबह की चाय बहुत पसंद है।",
]

result_orig = orig.analyze(test_lines, fake_encode)
result_no_rand = no_rand.analyze(test_lines, fake_encode)

print("original (with unused random.seed): ", result_orig)
print("no_random (random import/seed removed):", result_no_rand)
print()
print("IDENTICAL:" , result_orig == result_no_rand)
