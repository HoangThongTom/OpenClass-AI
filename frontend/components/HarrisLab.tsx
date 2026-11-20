"use client";
import { useState } from "react";
import { Activity, Info, SlidersHorizontal, Sigma } from "lucide-react";

const examples = [
  { name: "Vùng phẳng", subtitle: "Ít gradient ở cả hai chiều", e1: 0.3, e2: 0.3, color: "cyan" },
  { name: "Cạnh", subtitle: "Chỉ một hướng có gradient lớn", e1: 30, e2: 0.6, color: "orange" },
  { name: "Góc", subtitle: "Hai hướng đều có gradient lớn", e1: 18, e2: 14, color: "purple" },
];

export function HarrisLab() {
  const [k, setK] = useState(0.04);
  const [selected, setSelected] = useState(2);
  const item = examples[selected];
  const det = item.e1 * item.e2;
  const trace = item.e1 + item.e2;
  const response = det - k * trace * trace;
  const verdict = response > 10 ? "GÓC" : response < -2 ? "CẠNH" : "VÙNG PHẲNG / YẾU";
  return <div className="lab-layout">
    <div className="lab-intro"><span className="eyebrow">INTERACTIVE VISION LAB</span><h2>Harris Corner Explorer<span className="title-period">.</span></h2><p>Điều chỉnh hệ số <b>k</b> và quan sát sự thay đổi của Harris response. Các trị riêng dưới đây là <strong>giá trị minh họa</strong>, không được tính từ ảnh thật.</p></div>
    <div className="lab-picker">{examples.map((example, index) => <button key={example.name} className={`lab-case ${selected === index ? "selected" : ""}`} onClick={() => setSelected(index)}><span className={`lab-pattern pattern-${index}`}><i/><i/><i/><i/></span><strong>{example.name}</strong><small>{example.subtitle}</small></button>)}</div>
    <div className="lab-workspace"><div className="lab-control-card"><div className="lab-card-heading"><SlidersHorizontal size={19}/><strong>Tham số thuật toán</strong></div><label htmlFor="kRange">Hệ số Harris <b>k = {k.toFixed(3)}</b></label><input id="kRange" type="range" min={0.04} max={0.10} step={0.005} value={k} onChange={e => setK(parseFloat(e.target.value))}/><div className="range-labels"><span>0.040</span><span>0.100</span></div><div className="lab-formula"><span>HARRIS RESPONSE</span><strong>R = det(M) − k · trace(M)²</strong><small>R = {det.toFixed(2)} − {k.toFixed(3)} × {trace.toFixed(2)}²</small></div></div><div className="lab-result-card"><div className="lab-card-heading"><Activity size={19}/><strong>Phản hồi trực tiếp</strong></div><div className="lab-response-number">{response.toFixed(2)}<span>R SCORE</span></div><span className={`lab-verdict ${verdict === "GÓC" ? "corner" : verdict === "CẠNH" ? "edge" : "flat"}`}>{verdict}</span><div className="eigen-row"><span>λ₁ = {item.e1}</span><span>λ₂ = {item.e2}</span></div><div className="eigen-bars"><div><span style={{ width: `${(item.e1 / 30) * 100}%` }}/></div><div><span style={{ width: `${(item.e2 / 30) * 100}%` }}/></div></div></div></div>
    <div className="lab-note"><Info size={18}/><p>Trong thuật toán Harris thật, M được xây từ gradient ảnh và trọng số cửa sổ. Để phát hiện góc, cần thêm ngưỡng phản hồi và non-maximum suppression. Ngưỡng ở mô phỏng này chỉ mang tính minh họa.</p></div>
  </div>;
}
