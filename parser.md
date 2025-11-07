# Sketch diagram for the Excel Parser Service

Perfect — here’s a **focused internal sketch** for the core logic of
**[Excel Parser Microservice (Java + Apache POI)]**.
This shows each main component/module and data flow inside the service:

---

## 🛠️ Sketch: Excel Parser Microservice (Java + Apache POI)

```mermaid
flowchart TD
    A1([HTTP/gRPC Request Handler])
    A2([File Uploader / Path Resolver])
    A3([POI Workbook Loader])
    A4([Sheet Enumerator])
    A5([Cell & Region Extractor])
    A6([Metadata Extractor])
    A7([Data Normalizer & Type Inferencer])
    A8([Output Formatter: JSON/Arrow Builder])
    A9([Error Handler / Logger])
    A10([Exporter: IPC Stream / File / Response])

    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> A5
    A5 --> A6
    A6 --> A7
    A7 --> A8
    A8 --> A10
    A1 --> A9
    A3 --> A9
    A5 --> A9
    A7 --> A9
    A10 --> A9
```

---

### **Component Breakdown**

* **HTTP/gRPC Request Handler**
  Accepts file uploads, file paths, request params (sheet selection, region, output type).

* **File Uploader / Path Resolver**
  Handles multipart uploads or fetches files from GCS/S3/local.

* **POI Workbook Loader**
  Loads workbook (`.xls`/`.xlsx`) with POI, handles password protection, encodings.

* **Sheet Enumerator**
  Iterates over all sheets, collects sheet-level metadata.

* **Cell & Region Extractor**
  Reads all rows/cells; detects data blocks, merged cells, formula cells, rich text.

* **Metadata Extractor**
  Gathers styles, named ranges, comments, document properties.

* **Data Normalizer & Type Inferencer**
  Standardizes values, infers types per column, fills nulls, validates ranges.

* **Output Formatter: JSON/Arrow Builder**
  Serializes to:

  * Structured JSON (schema, metadata, data arrays)
  * Arrow Table (via Java Arrow, if enabled)

* **Exporter: IPC Stream / File / Response**
  Returns data as HTTP/gRPC response, writes to disk, or streams Arrow IPC.

* **Error Handler / Logger**
  Captures and logs all errors, edge cases, and operational telemetry.

---

### 💡 **Notes**

* You can extend by plugging in **profiling, validation, or human-in-the-loop modules** before export.
* Optional: add a **config module** (e.g., sheet inclusion, column filters, safe mode for PII).

---

Let me know if you want a **Java package/folder structure** or an **OpenAPI endpoint spec** for this microservice!
