# Experiment 3: alternative implementations

Within group (cross mechanism) mean functional similarity 0.9582 against cross group baseline 0.6526; within group mean implementation similarity 0.8330 against cross group 0.8485.

## Canonical requirement onto the legacy personas

| canonical to legacy provider | kind | transport | input renames | output renames |
| --- | --- | --- | --- | --- |
| AR-PatReg | API | http | patient_mrn -> pat_no, full_name -> pat_name | pat_reg -> patient_id |
| AR-PatRowWrite | DATABASE | sqlite | patient_mrn -> pat_no, full_name -> pat_name | row_id -> patient_id [to_string] |
| AR-PatRegForm | GUI | form | patient_mrn -> pat_no, full_name -> pat_name | pat_reg -> patient_id |

## Groups

### register a patient in the legacy vocabulary (hospital_alias)

| pair | kinds | functional | implementation | full cosine | mapper total | kind match |
| --- | --- | --- | --- | --- | --- | --- |
| AR-PatReg -> AR-PatRowWrite | API to DATABASE | 0.9338 | 0.7704 | 0.8640 | 0.6231 | no |
| AR-PatReg -> AR-PatRegForm | API to GUI | 0.9949 | 0.8669 | 0.9131 | 0.8162 | no |
| AR-PatRowWrite -> AR-PatReg | DATABASE to API | 0.9338 | 0.7704 | 0.8640 | 0.6231 | no |
| AR-PatRowWrite -> AR-PatRegForm | DATABASE to GUI | 0.9321 | 0.7903 | 0.8734 | 0.5248 | no |
| AR-PatRegForm -> AR-PatReg | GUI to API | 0.9949 | 0.8669 | 0.9131 | 0.8162 | no |
| AR-PatRegForm -> AR-PatRowWrite | GUI to DATABASE | 0.9321 | 0.7903 | 0.8734 | 0.5248 | no |

Partition table, per block cosine against AR-PatReg:

| block | AR-PatReg | AR-PatRowWrite | AR-PatRegForm |
| --- | --- | --- | --- |
| availability | 1.0000 | 1.0000 | 1.0000 |
| delta | 1.0000 | 1.0000 | 1.0000 |
| effects | 1.0000 | 0.9423 | 0.9759 |
| inputs | 1.0000 | 1.0000 | 1.0000 |
| mechanism | 1.0000 | 0.8544 | 0.9495 |
| outputs | 1.0000 | 0.5021 | 1.0000 |
| preconditions | 0.0000 | 0.0000 | 0.0000 |
| quality | 1.0000 | 0.9907 | 0.9953 |
| reliability | 1.0000 | 1.0000 | 1.0000 |
| resources | 1.0000 | 0.8911 | 0.8911 |
| type | 1.0000 | 0.0000 | 0.0000 |

Adapter synthesis from AR-PatReg:

| requirement to provider | kinds | transport | input renames | output renames |
| --- | --- | --- | --- | --- |
| AR-PatReg -> AR-PatRowWrite | API to DATABASE | sqlite | pat_no -> pat_no, pat_name -> pat_name | row_id -> pat_reg [to_string] |
| AR-PatReg -> AR-PatRegForm | API to GUI | form | pat_no -> pat_no, pat_name -> pat_name | pat_reg -> pat_reg |

### register a patient in the canonical vocabulary (hospital_alias)

| pair | kinds | functional | implementation | full cosine | mapper total | kind match |
| --- | --- | --- | --- | --- | --- | --- |
| AR-RegisterPatient -> AR-RegistrationForm | API to GUI | 0.9816 | 0.9211 | 0.8880 | 0.6946 | no |
| AR-RegistrationForm -> AR-RegisterPatient | GUI to API | 0.9816 | 0.9211 | 0.8880 | 0.6946 | no |

Partition table, per block cosine against AR-RegisterPatient:

| block | AR-RegisterPatient | AR-RegistrationForm |
| --- | --- | --- |
| availability | 1.0000 | 1.0000 |
| delta | 1.0000 | 1.0000 |
| effects | 1.0000 | 0.9134 |
| inputs | 1.0000 | 1.0000 |
| mechanism | 1.0000 | 0.7218 |
| outputs | 1.0000 | 1.0000 |
| preconditions | 0.0000 | 0.0000 |
| quality | 1.0000 | 0.9953 |
| reliability | 1.0000 | 1.0000 |
| resources | 1.0000 | 0.8911 |
| type | 1.0000 | 0.0000 |

Adapter synthesis from AR-RegisterPatient:

| requirement to provider | kinds | transport | input renames | output renames |
| --- | --- | --- | --- | --- |
| AR-RegisterPatient -> AR-RegistrationForm | API to GUI | form | patient_mrn -> patient_mrn, full_name -> full_name | patient_id -> patient_id |

### place the order of the current cart (ecommerce_purchase)

| pair | kinds | functional | implementation | full cosine | mapper total | kind match |
| --- | --- | --- | --- | --- | --- | --- |
| EC-PlaceOrder -> EC-CheckoutForm | API to GUI | 0.9564 | 0.8689 | 0.8704 | 0.8299 | no |
| EC-CheckoutForm -> EC-PlaceOrder | GUI to API | 0.9564 | 0.8689 | 0.8704 | 0.8299 | no |

Partition table, per block cosine against EC-PlaceOrder:

| block | EC-PlaceOrder | EC-CheckoutForm |
| --- | --- | --- |
| availability | 1.0000 | 1.0000 |
| delta | 1.0000 | 0.8841 |
| effects | 1.0000 | 0.8424 |
| inputs | 1.0000 | 1.0000 |
| mechanism | 1.0000 | 0.5612 |
| outputs | 1.0000 | 1.0000 |
| preconditions | 1.0000 | 1.0000 |
| quality | 1.0000 | 0.9971 |
| reliability | 1.0000 | 1.0000 |
| resources | 1.0000 | 1.0000 |
| type | 1.0000 | 0.0000 |

Adapter synthesis from EC-PlaceOrder:

| requirement to provider | kinds | transport | input renames | output renames |
| --- | --- | --- | --- | --- |
| EC-PlaceOrder -> EC-CheckoutForm | API to GUI | form | payment_method -> payment_method | order_id -> order_id |

### accept an uploaded document into the pipeline (document_processing)

| pair | kinds | functional | implementation | full cosine | mapper total | kind match |
| --- | --- | --- | --- | --- | --- | --- |
| DOC-UploadDocument -> DOC-UploadForm | FILE to GUI | 0.9344 | 0.8165 | 0.8291 | 0.7097 | no |
| DOC-UploadDocument -> DOC-IntakeHandler | FILE to EVENT | 0.9393 | 0.8542 | 0.8722 | 0.7880 | no |
| DOC-UploadForm -> DOC-UploadDocument | GUI to FILE | 0.9344 | 0.8165 | 0.8291 | 0.7097 | no |
| DOC-UploadForm -> DOC-IntakeHandler | GUI to EVENT | 0.9929 | 0.7755 | 0.8852 | 0.8587 | no |
| DOC-IntakeHandler -> DOC-UploadDocument | EVENT to FILE | 0.9393 | 0.8542 | 0.8722 | 0.7880 | no |
| DOC-IntakeHandler -> DOC-UploadForm | EVENT to GUI | 0.9929 | 0.7755 | 0.8852 | 0.8587 | no |

Partition table, per block cosine against DOC-UploadDocument:

| block | DOC-UploadDocument | DOC-UploadForm | DOC-IntakeHandler |
| --- | --- | --- | --- |
| availability | 1.0000 | 1.0000 | 1.0000 |
| delta | 1.0000 | 1.0000 | 1.0000 |
| effects | 1.0000 | 0.9655 | 0.9835 |
| inputs | 1.0000 | 1.0000 | 1.0000 |
| mechanism | 1.0000 | 0.8588 | 0.9623 |
| outputs | 1.0000 | 0.4382 | 0.4382 |
| preconditions | 0.0000 | 0.0000 | 0.0000 |
| quality | 1.0000 | 0.9799 | 0.9997 |
| reliability | 1.0000 | 1.0000 | 1.0000 |
| resources | 1.0000 | 0.4416 | 0.8643 |
| type | 1.0000 | 0.0000 | 0.0000 |

Adapter synthesis from DOC-UploadDocument:

| requirement to provider | kinds | transport | input renames | output renames |
| --- | --- | --- | --- | --- |
| DOC-UploadDocument -> DOC-UploadForm | FILE to GUI | form | source_name -> source_name | accepted -> file_path [to_string] |
| DOC-UploadDocument -> DOC-IntakeHandler | FILE to EVENT | local | source_name -> source_name | accepted -> file_path [to_string] |

