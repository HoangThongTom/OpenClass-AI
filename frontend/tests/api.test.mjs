import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import ts from "typescript";

const source = await readFile(new URL("../lib/api.ts", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
});
const { api } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`);

test("regenerate sends the selected model and slide count", async t => {
  let sent;
  t.mock.method(globalThis, "fetch", async (url, options) => {
    sent = { url, ...options };
    return Response.json({ id: "lesson", model: "qwen2.5:3b", slide_count: 2 });
  });
  const result = await api.regenerate("lesson", { model: "qwen2.5:3b", slide_count: 2 });
  assert.equal(sent.url, "/api/lessons/lesson/generate");
  assert.equal(sent.method, "POST");
  assert.equal(sent.headers["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(sent.body), { model: "qwen2.5:3b", slide_count: 2 });
  assert.equal(result.model, "qwen2.5:3b");
});

test("create retains multipart uploads for multiple documents", async t => {
  const form = new FormData();
  form.append("files", new Blob(["PDF"], { type: "application/pdf" }), "one.pdf");
  form.append("files", new Blob(["# Notes"]), "two.md");
  t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(url, "/api/lessons");
    assert.equal(options.body, form);
    assert.deepEqual(options.body.getAll("files").map(file => file.name), ["one.pdf", "two.md"]);
    return Response.json({ id: "lesson" }, { status: 202 });
  });
  assert.equal((await api.create(form)).id, "lesson");
});

test("model validation errors reach the UI with their message", async t => {
  t.mock.method(globalThis, "fetch", async () => Response.json(
    { detail: "Model chưa có trong Ollama." }, { status: 400 },
  ));
  await assert.rejects(api.regenerate("lesson", { model: "missing", slide_count: 3 }), /Model chưa có trong Ollama/);
});

test("outline approval submits the edited outline", async t => {
  const outline = { summary: "Harris", slides: [{ title: "Edited", focus: "Corners" }, { title: "ANMS", focus: "Suppression" }] };
  t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(url, "/api/lessons/lesson/approve");
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), outline);
    return Response.json({ status: "generating" });
  });
  assert.equal((await api.approve("lesson", outline)).status, "generating");
});

test("resume and single-slide regeneration address the saved lesson", async t => {
  const urls = [];
  t.mock.method(globalThis, "fetch", async (url, options) => {
    urls.push(url); assert.equal(options.method, "POST");
    return Response.json({ status: "generating" });
  });
  await api.resume("lesson");
  await api.regenerateSlide("lesson", 2);
  assert.deepEqual(urls, ["/api/lessons/lesson/resume", "/api/lessons/lesson/slides/2/generate"]);
});

test("field validation errors explain invalid slide input", async t => {
  t.mock.method(globalThis, "fetch", async () => Response.json(
    { detail: [{ msg: "At most 5 bullets" }] }, { status: 422 },
  ));
  await assert.rejects(api.editSlide("lesson", 0, {}), /Dữ liệu chưa hợp lệ: At most 5 bullets/);
});
