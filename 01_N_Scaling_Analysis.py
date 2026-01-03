
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit import QuantumCircuit, transpile
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# ------------------------------
# 1. الاتصال بـ IBM Quantum باستخدام المفتاح الجديد
# ------------------------------
API_KEY = "uoOnLmmSOD4Zkpuy5sb1ZGTrFwD65LD1nuV-2LumeuVq"
service = QiskitRuntimeService(channel="ibm_quantum_platform", token=API_KEY, instance="open-instance")
backend_name = "ibm_torino"
backend = service.backend(backend_name)
print(f"Connected to backend: {backend.name}")

# ------------------------------
# 2. إعداد التجارب
# ------------------------------
network_sizes = [5, 10, 20, 40]
shots_per_circuit = 1024
window_predictive = 10  # حجم النافذة للتصحيح التنبؤي

def predictive_correction(signal, window=10):
    """تصحيح تنبؤي ديناميكي على المتسلسلة"""
    corrected = np.copy(signal)
    for i in range(window, len(signal)):
        predicted = np.mean(corrected[i-window:i])
        corrected[i] -= predicted * 0.5
    return corrected

results_dynamic = []

# ------------------------------
# 3. تشغيل المحاكاة الديناميكية لكل network size
# ------------------------------
for N in network_sizes:
    print(f"▶ Running simulation for N={N}")
    qc = QuantumCircuit(N)
    qc.h(range(N))
    qc.measure_all()

    isa_circuit = transpile(qc, backend=backend, optimization_level=1)
    sampler = Sampler(mode=backend)
    job = sampler.run([isa_circuit], shots=shots_per_circuit)
    result = job.result()[0]
    counts = result.data.meas.get_counts()

    # ------------------------------
    # 4. بناء مصفوفة Δt لكل qubit عبر shots
    # ------------------------------
    qubit_time_series = np.zeros((N, shots_per_circuit))
    shot_index = 0
    for bitstring, count in counts.items():
        for _ in range(count):
            qubit_time_series[:, shot_index] = np.array([int(b) for b in bitstring])
            shot_index += 1

    # ------------------------------
    # 5. تطبيق التصحيح التنبؤي لكل qubit
    # ------------------------------
    corrected_series = np.zeros_like(qubit_time_series)
    for q in range(N):
        corrected_series[q] = predictive_correction(qubit_time_series[q], window=window_predictive)

    # ------------------------------
    # 6. الإحصائيات
    # ------------------------------
    mean_raw = np.mean(qubit_time_series, axis=1)
    std_raw = np.std(qubit_time_series, axis=1)
    mean_corr = np.mean(corrected_series, axis=1)
    std_corr = np.std(corrected_series, axis=1)

    results_dynamic.append({
        "N": N,
        "Mean_Raw": mean_raw,
        "Std_Raw": std_raw,
        "Mean_Corr": mean_corr,
        "Std_Corr": std_corr,
        "Raw_Series": qubit_time_series,
        "Corrected_Series": corrected_series
    })

# ------------------------------
# 7. عرض النتائج
# ------------------------------
for res in results_dynamic:
    N = res["N"]
    print(f"\n📊 Network size: {N}")
    print(f"Mean Raw per qubit: {res['Mean_Raw']}")
    print(f"Std Raw per qubit: {res['Std_Raw']}")
    print(f"Mean Corrected per qubit: {res['Mean_Corr']}")
    print(f"Std Corrected per qubit: {res['Std_Corr']}")

# ------------------------------
# 8. رسم تطور الزمن لكل qubit
# ------------------------------
for res in results_dynamic:
    N = res["N"]
    plt.figure(figsize=(12,6))
    for q in range(N):
        plt.plot(res["Corrected_Series"][q], alpha=0.6)
    plt.title(f"Dynamic Time Shift per Qubit after Predictive Correction | N={N}")
    plt.xlabel("Shot Index")
    plt.ylabel("Δt (Corrected)")
    plt.grid(True)
    plt.show()

# ------------------------------
# 9. خريطة حرارية لكل network size
# ------------------------------
for res in results_dynamic:
    N = res["N"]
    plt.figure(figsize=(12,4))
    sns.heatmap(res["Corrected_Series"], cmap='coolwarm', cbar_kws={'label': 'Δt'})
    plt.title(f"Heatmap of Corrected Quantum Time Shift | N={N}")
    plt.xlabel("Shot Index")
    plt.ylabel("Qubit Index")
    plt.show()
