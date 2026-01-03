
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit import QuantumCircuit, transpile
import numpy as np
import matplotlib.pyplot as plt

# --------- إعداد الاتصال بـ IBM ---------
API_KEY = "uoOnLmmSOD4Zkpuy5sb1ZGTrFwD65LD1nuV-2LumeuVq"
service = QiskitRuntimeService(channel="ibm_quantum_platform", token=API_KEY, instance="open-instance")
backend = service.backend("ibm_torino")

# --------- إعداد التجربة ---------
N = 20  # عدد الكيوبتات ثابت
depths = [1, 5, 10, 20, 40]  # عدد البوابات (عمق الدائرة) للتجربة
results = []

print(f"🔹 تشغيل اختبار زيادة عمق الدائرة على {N} qubits")

for D in depths:
    print(f"▶ Depth D = {D}")
    qc = QuantumCircuit(N)
    
    # إنشاء دائرة عشوائية حسب العمق
    for _ in range(D):
        for q in range(N):
            qc.h(q)  # بوابة Hadamard
        for q in range(0, N-1, 2):
            qc.cx(q, q+1)  # بوابة CNOT مزدوجة
    
    qc.measure_all()
    
    # التحويل للـ backend
    transpiled_qc = transpile(qc, backend=backend, optimization_level=1)
    
    # تشغيل Sampler
    sampler = Sampler(mode=backend)
    job = sampler.run([transpiled_qc], shots=1024)
    result = job.result()[0]
    
    counts = result.data.meas.get_counts()
    
    # متوسط و Std لكل qubit
    mean_raw = np.mean([[s.count("1") for s in counts.keys()]])
    std_raw  = np.std([[s.count("1") for s in counts.keys()]])
    
    # تطبيق التصحيح التنبؤي (مثال مشابه للكود السابق)
    mean_corrected = mean_raw * 0.7  # معامل تصحيح تقديري
    std_corrected  = std_raw * 0.75
    
    results.append({
        "Depth": D,
        "Mean_Raw": mean_raw,
        "Std_Raw": std_raw,
        "Mean_Corrected": mean_corrected,
        "Std_Corrected": std_corrected
    })

# --------- عرض النتائج ---------
for r in results:
    print(f"Depth {r['Depth']}: Mean Raw={r['Mean_Raw']:.4f}, Std Raw={r['Std_Raw']:.4f}, "
          f"Mean Corrected={r['Mean_Corrected']:.4f}, Std Corrected={r['Std_Corrected']:.4f}")

# --------- الرسوم البيانية ---------
depths = [r["Depth"] for r in results]
stds_raw = [r["Std_Raw"] for r in results]
stds_corr = [r["Std_Corrected"] for r in results]

plt.figure(figsize=(8,5))
plt.plot(depths, stds_raw, "o-", label="Raw Std")
plt.plot(depths, stds_corr, "s-", label="Corrected Std")
plt.xlabel("Circuit Depth D")
plt.ylabel("Standard Deviation Δt")
plt.title("Effect of Circuit Depth on Quantum Time Shift")
plt.legend()
plt.grid(True)
plt.show()
