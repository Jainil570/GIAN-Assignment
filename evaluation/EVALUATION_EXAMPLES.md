# Evaluation examples

Model: **qwen2.5:7b-instruct-q4_K_M (local, via Ollama)** | Embeddings: **BAAI/bge-m3 (1024-d)** | Vector DB: **PostgreSQL + pgvector**

Automatic checks passed: **23/23** (answerable: 18/18, must-refuse: 5/5).

Each check verifies the expected behaviour (answer vs. the exact insufficiency sentence), required facts in the answer and the cited source document. Retrieval trace = the excerpts given to the model with their dense similarity and which signals found them.

---
## Q01 - innovator / technique (51st)
**Question:** Who developed a method to grow trees with just one litre of water, and how does it work?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 23.39 s

### Answer
Shri Sundaram Ji developed a method to grow trees with just one litre of water, ensuring survival without further watering [S1]. This technique involves deep ploughing the field during the first rain, breaking capillaries when the last rain comes, making pits, planting saplings, and adding one litre of water [S2].

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Sundaram Verma (written here as "Shri Sundaram Ji")
- **Innovation:** Growing trees with one litre of water (Sundaram Verma)
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (3) July - September 2024 - "51st Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani | Rajasthan : Part-I"
- **Page/Record:** Honey Bee Vol 35 (3) July - September 2024, p. 14 (PDF page 2 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)
- **Notes:** a name in this excerpt is spelled differently in other places in the sources

**Source 2 [S2]**
- **Innovator:** Sundaram Verma (written here as "Sunda Ram Verma")
- **Innovation:** Growing trees with one litre of water (Sundaram Verma)
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (4) October - December 2024 - "The pain behind the glitter! 51 Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani, Nagaur | Rajasthan : Part-II"
- **Page/Record:** Honey Bee Vol 35 (4) October - December 2024, pp. 3-4 (PDF pages 5-6 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)
- **Notes:** a name in this excerpt is spelled differently in other places in the sources

### Entities identified
- Growing trees with one litre of water (Sundaram Verma) (innovation, `INN-ONE-LITRE-TREE`) - from question
- Sundaram Verma (person, `PER-SUNDARAM-VERMA`) - from answer [S1]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY51-HB-P1-C02 | Honey Bee Vol 35 (3) July - September 2024, p. 14 (PDF page 2 of '51-s | 0.472 | 2 | 2 | INN-ONE-LITRE-TREE |
| S2 | SY51-HB-P2-C05 | Honey Bee Vol 35 (4) October - December 2024, pp. 3-4 (PDF pages 5-6 o | 0.468 | 3 | 5 | INN-ONE-LITRE-TREE |
| S3 | GIAN-NIDHI-R0276 | GIAN Nidhi record ID 276 | 0.5 | 1 | 4 |  |
| S4 | GIAN-NIDHI-R0109 | GIAN Nidhi record ID 109 | 0.443 | 6 | 1 |  |
| S5 | GIAN-NIDHI-R0550 | GIAN Nidhi record ID 550 | 0.433 | 7 | 18 |  |
| S6 | GIAN-NIDHI-R0364 | GIAN Nidhi record ID 364 | 0.417 | 16 | 7 |  |

Gate: `{"max_dense": 0.5, "specific_entities": ["INN-ONE-LITRE-TREE"], "top_term_coverage": 0.89, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q02 - event / organisations (51st)
**Question:** Who organised and who supported the 51st Shodhyatra, and when and where did it take place?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 16.05 s

### Answer
The 51st Shodhyatra was organized by SRISTI, supported by GIAN and the Honey Bee Network [S1]. It took place from June 17-23, 2024, in Harima to Chak Dhani, Nagaur, Rajasthan [S1].

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Not specified in this source
- **Innovation:** Not specified in this source
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (4) October - December 2024 - "The pain behind the glitter! 51 Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani, Nagaur | Rajasthan : Part-II"
- **Page/Record:** Honey Bee Vol 35 (4) October - December 2024, p. 2 (PDF page 4 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)

### Entities identified
- 51st Shodhyatra (June 17-23, 2024, Harima to Chak Dhani, Nagaur, Rajasthan) (event, `EVT-SY51`) - from question
- Shodhyatra (series) (event_series, `EVT-SHODHYATRA-SERIES`) - from answer [S1]
- GIAN (organisation, `ORG-GIAN`) - from answer [S1]
- Honey Bee Network (organisation, `ORG-HBN`) - from answer [S1]
- SRISTI (organisation, `ORG-SRISTI`) - from answer [S1]
- Nagaur (Rajasthan) (place, `PLC-NAGAUR`) - from answer [S1]
- Rajasthan (place, `PLC-RAJASTHAN`) - from answer [S1]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY51-HB-P2-C01 | Honey Bee Vol 35 (4) October - December 2024, p. 2 (PDF page 4 of '51- | 0.531 | 2 | 30 | EVT-SY51 |
| S2 | SY51-HB-P1-C01 | Honey Bee Vol 35 (3) July - September 2024, p. 13 (PDF page 1 of '51-s | 0.495 | 9 | 16 | EVT-SY51 |
| S3 | SY51-HB-P1-C07 | Honey Bee Vol 35 (3) July - September 2024, p. 15 (PDF page 3 of '51-s | 0.527 | 4 | None | EVT-SY51 |
| S4 | SY51-HB-P1-C06 | Honey Bee Vol 35 (3) July - September 2024, p. 15 (PDF page 3 of '51-s | 0.508 | 8 | None | EVT-SY51 |
| S5 | SY51-HB-P2-C04 | Honey Bee Vol 35 (4) October - December 2024, p. 3 (PDF page 5 of '51- | 0.489 | 10 | None | EVT-SY51 |
| S6 | SY51-HB-P2-C02 | Honey Bee Vol 35 (4) October - December 2024, pp. 2-3 (PDF pages 4-5 o | 0.511 | 7 | 27 | EVT-SY51 |

Gate: `{"max_dense": 0.531, "specific_entities": ["EVT-SY51"], "top_term_coverage": 0.43, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q03 - name variants (51st)
**Question:** Who developed the thornless Khejri, and is the innovator's name written the same way in both parts of the article?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 2.42 s

### Answer
No - the sources do not write this name the same way: "Rameshwar Lal ji" (Honey Bee Vol 35 (4) October - December 2024, pp. 3-4 [S1]; Honey Bee Vol 35 (4) October - December 2024, pp. 2-3 [S2]) vs "Shri Rameshwar Prasad Ji" (Honey Bee Vol 35 (3) July - September 2024, p. 14 [S3]). All of these mentions credit the person with: Thornless Khejri through grafting. The sources do not say which spelling is correct.

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Rameshwar Lal / Rameshwar Prasad (name differs between Part I and Part II) (written here as "Rameshwar Lal ji")
- **Innovation:** Thornless Khejri through grafting (written here as "grafting khejri")
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (4) October - December 2024 - "The pain behind the glitter! 51 Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani, Nagaur | Rajasthan : Part-II"
- **Page/Record:** Honey Bee Vol 35 (4) October - December 2024, pp. 3-4 (PDF pages 5-6 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)
- **Notes:** a name in this excerpt is spelled differently in other places in the sources

**Source 2 [S2]**
- **Innovator:** Rameshwar Lal / Rameshwar Prasad (name differs between Part I and Part II) (written here as "Mr. Rameshwar Lal ji")
- **Innovation:** Thornless Khejri through grafting (written here as "thornless variety of the Khejri tree")
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (4) October - December 2024 - "The pain behind the glitter! 51 Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani, Nagaur | Rajasthan : Part-II"
- **Page/Record:** Honey Bee Vol 35 (4) October - December 2024, pp. 2-3 (PDF pages 4-5 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)
- **Notes:** a name in this excerpt is spelled differently in other places in the sources

**Source 3 [S3]**
- **Innovator:** Rameshwar Lal / Rameshwar Prasad (name differs between Part I and Part II) (written here as "Shri Rameshwar Prasad Ji")
- **Innovation:** Thornless Khejri through grafting (written here as "grafting techniques with the Khejri tree")
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (3) July - September 2024 - "51st Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani | Rajasthan : Part-I"
- **Page/Record:** Honey Bee Vol 35 (3) July - September 2024, p. 14 (PDF page 2 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)
- **Notes:** a name in this excerpt is spelled differently in other places in the sources

### Entities identified
- Thornless Khejri through grafting (innovation, `INN-THORNLESS-KHEJRI`) - from question
- Rameshwar Lal / Rameshwar Prasad (name differs between Part I and Part II) (person, `PER-RAMESHWAR-KHEJRI`) - from answer [S1]
- Khejri tree (Prosopis cineraria) (plant, `PLT-KHEJRI`) - from answer [S2]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY51-HB-P2-C05 | Honey Bee Vol 35 (4) October - December 2024, pp. 3-4 (PDF pages 5-6 o | 0.533 | 1 | 19 | INN-THORNLESS-KHEJRI |
| S2 | SY51-HB-P2-C02 | Honey Bee Vol 35 (4) October - December 2024, pp. 2-3 (PDF pages 4-5 o | 0.472 | 4 | 16 | INN-THORNLESS-KHEJRI |
| S3 | SY51-HB-P1-C02 | Honey Bee Vol 35 (3) July - September 2024, p. 14 (PDF page 2 of '51-s | 0.513 | 2 | None | INN-THORNLESS-KHEJRI |
| S4 | GIAN-NIDHI-R0376 | GIAN Nidhi record ID 376 | 0.448 | 30 | 3 |  |
| S5 | GIAN-NIDHI-R0056 | GIAN Nidhi record ID 56 | 0.449 | 25 | 7 |  |
| S6 | GIAN-NIDHI-R0608 | GIAN Nidhi record ID 608 | 0.498 | 3 | None |  |

Gate: `{"max_dense": 0.533, "specific_entities": ["INN-THORNLESS-KHEJRI"], "top_term_coverage": 0.43, "lexical_hits": 30, "pass": true}`  
Verification: attempts=0, remaining problems=[], removed sentences=[]

</details>

---
## Q04 - conflicting values (51st)
**Question:** How many sweet potato varieties are attributed to Panchariya?

**Expected:** answer | **Check:** PASS (ok) | **Status:** partial | **Time:** 12.77 s

### Answer
The available sources do not provide a consistent number of sweet potato varieties attributed to Panchariya. According to one source, Rahulchand Panchariya showcased eight varieties of sweet potatoes [S3]. However, another source mentions that Rawalchand Panchariya developed five varieties of sweet potatoes [S2].

### Relevant Information
**Source 1 [S3]**
- **Innovator:** Rawalchand / Rahulchand Panchariya
- **Innovation:** Organic, low-water sweet potato varieties (Panchariya) (written here as "sweet potatoes")
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (3) July - September 2024 - "51st Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani | Rajasthan : Part-I"
- **Page/Record:** Honey Bee Vol 35 (3) July - September 2024, p. 15 (PDF page 3 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)
- **Notes:** a name in this excerpt is spelled differently in other places in the sources

**Source 2 [S2]**
- **Innovator:** Rawalchand / Rahulchand Panchariya (written here as "Rawalchand Panchariya")
- **Innovation:** Organic, low-water sweet potato varieties (Panchariya) (written here as "sweet potatoes")
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (4) October - December 2024 - "The pain behind the glitter! 51 Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani, Nagaur | Rajasthan : Part-II"
- **Page/Record:** Honey Bee Vol 35 (4) October - December 2024, p. 4 (PDF page 6 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)
- **Notes:** a name in this excerpt is spelled differently in other places in the sources

### Entities identified
- Organic, low-water sweet potato varieties (Panchariya) (innovation, `INN-SWEET-POTATO-VARIETIES`) - from question
- Rawalchand / Rahulchand Panchariya (person, `PER-PANCHARIYA`) - from answer [S3]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY51-HB-P1-C02 | Honey Bee Vol 35 (3) July - September 2024, p. 14 (PDF page 2 of '51-s | 0.547 | 1 | 3 | INN-SWEET-POTATO-VARIETIES |
| S2 | SY51-HB-P2-C06 | Honey Bee Vol 35 (4) October - December 2024, p. 4 (PDF page 6 of '51- | 0.545 | 2 | 2 | INN-SWEET-POTATO-VARIETIES |
| S3 | SY51-HB-P1-C07 | Honey Bee Vol 35 (3) July - September 2024, p. 15 (PDF page 3 of '51-s | 0.503 | 3 | 5 | INN-SWEET-POTATO-VARIETIES |
| S4 | SY51-HB-P2-C02 | Honey Bee Vol 35 (4) October - December 2024, pp. 2-3 (PDF pages 4-5 o | 0.478 | 4 | 4 | INN-SWEET-POTATO-VARIETIES |
| S5 | SY53-PPT-U22 | 53rd Shodhyatra presentation, slides 40-43 | 0.457 | 6 | 1 |  |
| S6 | SY53-PPT-U24 | 53rd Shodhyatra presentation, slide 46 | 0.47 | 5 | 6 |  |

Gate: `{"max_dense": 0.547, "specific_entities": ["INN-SWEET-POTATO-VARIETIES"], "top_term_coverage": 0.8, "lexical_hits": 21, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q05 - image text (51st)
**Question:** Which places were on the route of the 51st Shodhyatra?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 12.31 s

### Answer
The route of the 51st Shodhyatra from Harima to Chak Dhani included the following places: Harima, Likhimdas Ji Mandir, Atusar, Firod, Amanda Ki Dhani, Mundwa, Bhadana, Kuchera and Chak Dhani [S3].

### Relevant Information
**Source 1 [S3]**
- **Innovator:** Not specified in this source
- **Innovation:** Not specified in this source
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (4) October - December 2024 - "The pain behind the glitter! 51 Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani, Nagaur | Rajasthan : Part-II"
- **Page/Record:** Honey Bee Vol 35 (4) October - December 2024, p. 3 (PDF page 5 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)
- **Notes:** part of this text was transcribed from an image (photo, graphic or newspaper clipping)

### Entities identified
- 51st Shodhyatra (June 17-23, 2024, Harima to Chak Dhani, Nagaur, Rajasthan) (event, `EVT-SY51`) - from question
- Shodhyatra (series) (event_series, `EVT-SHODHYATRA-SERIES`) - from answer [S3]
- Amanda Ki Dhani (place, `PLC-AMANDA-KI-DHANI`) - from answer [S3]
- Atusar (place, `PLC-ATUSAR`) - from answer [S3]
- Bhadana (place, `PLC-BHADANA`) - from answer [S3]
- Chak Dhani (place, `PLC-CHAK-DHANI`) - from answer [S3]
- Firod (place, `PLC-FIROD`) - from answer [S3]
- Harima (place, `PLC-HARIMA`) - from answer [S3]
- Kuchera (place, `PLC-KUCHERA`) - from answer [S3]
- Likhmidas Temple (place, `PLC-LIKHMIDAS-TEMPLE`) - from answer [S3]
- Mundwa (place, `PLC-MUNDWA`) - from answer [S3]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY51-HB-P1-C01 | Honey Bee Vol 35 (3) July - September 2024, p. 13 (PDF page 1 of '51-s | 0.503 | 7 | 15 | EVT-SY51 |
| S2 | SY51-HB-P2-C04 | Honey Bee Vol 35 (4) October - December 2024, p. 3 (PDF page 5 of '51- | 0.476 | 12 | 26 | EVT-SY51 |
| S3 | SY51-HB-P2-C08 | Honey Bee Vol 35 (4) October - December 2024, p. 3 (PDF page 5 of '51- | 0.505 | 6 | None | EVT-SY51 |
| S4 | SY51-HB-P1-C07 | Honey Bee Vol 35 (3) July - September 2024, p. 15 (PDF page 3 of '51-s | 0.505 | 5 | None | EVT-SY51 |
| S5 | SY51-HB-P1-C03 | Honey Bee Vol 35 (3) July - September 2024, p. 14 (PDF page 2 of '51-s | 0.477 | 11 | None | EVT-SY51 |
| S6 | SY51-HB-P2-C02 | Honey Bee Vol 35 (4) October - December 2024, pp. 2-3 (PDF pages 4-5 o | 0.491 | 9 | 27 | EVT-SY51 |

Gate: `{"max_dense": 0.505, "specific_entities": ["EVT-SY51"], "top_term_coverage": 0.67, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q06 - traditional knowledge (51st)
**Question:** What traditional remedies for animals did Kanaramji share?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 9.86 s

### Answer
Shree Kanaramji shared traditional remedies for animals, including using ground old bamboo boiled in water to help a cow with an umbilical cord issue and giving isabgol soaked in cold water for loose motion [S1].

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Kanaramji (91-year-old) (written here as "Shree Kanaramji")
- **Innovation:** Traditional animal remedies (Kanaramji) (written here as "traditional remedies for animals")
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (4) October - December 2024 - "The pain behind the glitter! 51 Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani, Nagaur | Rajasthan : Part-II"
- **Page/Record:** Honey Bee Vol 35 (4) October - December 2024, p. 4 (PDF page 6 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)
- **Notes:** a name in this excerpt is spelled differently in other places in the sources

### Entities identified
- Traditional animal remedies (Kanaramji) (traditional_knowledge, `INN-ANIMAL-REMEDIES-KANARAM`) - from question
- Kanaramji (91-year-old) (person, `PER-KANARAMJI`) - from question

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY51-HB-P2-C06 | Honey Bee Vol 35 (4) October - December 2024, p. 4 (PDF page 6 of '51- | 0.564 | 2 | 1 | INN-ANIMAL-REMEDIES-KANARAM, PER-KANARAMJI |
| S2 | SY51-HB-P1-C05 | Honey Bee Vol 35 (3) July - September 2024, pp. 14-15 (PDF pages 2-3 o | 0.61 | 1 | 4 | PER-KANARAMJI |
| S3 | SY51-HB-P2-C02 | Honey Bee Vol 35 (4) October - December 2024, pp. 2-3 (PDF pages 4-5 o | 0.501 | 3 | 7 | PER-KANARAMJI |
| S4 | SY53-PPT-U51 | 53rd Shodhyatra presentation, slide 87 | 0.412 | 9 | 5 |  |
| S5 | SY53-PPT-U14 | 53rd Shodhyatra presentation, slides 27-28 | 0.398 | 12 | 14 |  |
| S6 | SY53-PPT-U30 | 53rd Shodhyatra presentation, slide 53 | 0.41 | 10 | 24 |  |

Gate: `{"max_dense": 0.61, "specific_entities": ["INN-ANIMAL-REMEDIES-KANARAM", "PER-KANARAMJI"], "top_term_coverage": 1.0, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q07 - Hindi source, conflicting values (53rd)
**Question:** How heavy is the Noorjahan mango and who promoted it?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 8.41 s

### Answer
The Noorjahan mango weighs from 2 to 4.5 kilograms per mango, with some sources stating it can weigh up to 4.5 kilograms [S1]. Isak Mansuri promoted this variety by saving and conserving the 'Noorjahan' mango and working on its care and improvement for years [S1]. Note: the sources give different values for the weight of one Noorjahan mango: 2 to 4 kilos (slide 48 (description)) [S1]; 2 to 4.5 kilograms (slide 48 ('features' list)) [S1]; 3 to 4 kilograms (slide 49) [S1].

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Isak Mansuri
- **Innovation:** Noorjahan mango
- **Author:** Not stated in the source - No author or presenter is named on any slide. The PDF metadata field Author='Admin' is a generic account name and is not treated as an author.
- **Source:** 53rd Shodhyatra presentation (Hindi) - "53rd Shodhyatra: Bhurimati (Jhabua district, Madhya Pradesh) to Ambala (Chhota Udepur district, Gujarat), 04-10 June 2025"
- **Page/Record:** 53rd Shodhyatra presentation, slides 48-49 - [https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view](https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view)
- **Notes:** English text is a translation of the Hindi slide; the Hindi original is stored with the chunk; the source gives different values for the same fact - report each value

### Entities identified
- Noorjahan mango (crop_variety, `INN-NOORJAHAN-MANGO`) - from question
- Isak Mansuri (person, `PER-ISAK-MANSURI`) - from answer [S1]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY53-PPT-U26 | 53rd Shodhyatra presentation, slides 48-49 | 0.696 | 1 | 3 | INN-NOORJAHAN-MANGO |
| S2 | SY53-PPT-U24 | 53rd Shodhyatra presentation, slide 46 | 0.41 | 2 | None |  |
| S3 | SY51-HB-P1-C02 | Honey Bee Vol 35 (3) July - September 2024, p. 14 (PDF page 2 of '51-s | 0.398 | 3 | None |  |
| S4 | SY53-PPT-U30 | 53rd Shodhyatra presentation, slide 53 | 0.398 | 4 | None |  |
| S5 | GIAN-NIDHI-R0183 | GIAN Nidhi record ID 183 | 0.392 | 5 | None |  |
| S6 | SY53-PPT-U28 | 53rd Shodhyatra presentation, slide 51 | 0.39 | 6 | None |  |

Gate: `{"max_dense": 0.696, "specific_entities": ["INN-NOORJAHAN-MANGO"], "top_term_coverage": 0.8, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q08 - innovation (53rd)
**Question:** Who built a machine for breaking mahua seeds, and how successful was it in the field trials?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 9.52 s

### Answer
Shri Dharmveer built a hand-operated mahua seed breaking machine [S1]. In the field trials, the success rate of the machine was about 80%: some seeds broke more than necessary, and very small mahua fruits could not be broken fully [S1].

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Shri Dharmveer (Yamunanagar, Haryana)
- **Innovation:** Hand-operated mahua seed breaking machine (Shri Dharmveer)
- **Author:** Not stated in the source - No author or presenter is named on any slide. The PDF metadata field Author='Admin' is a generic account name and is not treated as an author.
- **Source:** 53rd Shodhyatra presentation (Hindi) - "53rd Shodhyatra: Bhurimati (Jhabua district, Madhya Pradesh) to Ambala (Chhota Udepur district, Gujarat), 04-10 June 2025"
- **Page/Record:** 53rd Shodhyatra presentation, slides 57-60 - [https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view](https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view)
- **Notes:** English text is a translation of the Hindi slide; the Hindi original is stored with the chunk

### Entities identified
- Hand-operated mahua seed breaking machine (Shri Dharmveer) (innovation, `INN-MAHUA-DECORTICATOR`) - from question
- Shri Dharmveer (Yamunanagar, Haryana) (person, `PER-DHARMVEER-SY53`) - from answer [S1]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY53-PPT-U33 | 53rd Shodhyatra presentation, slides 57-60 | 0.644 | 1 | 1 | INN-MAHUA-DECORTICATOR |
| S2 | SY53-PPT-U55 | 53rd Shodhyatra presentation, slide 91 | 0.565 | 2 | None | INN-MAHUA-DECORTICATOR |
| S3 | GIAN-NIDHI-R0011 | GIAN Nidhi record ID 11 | 0.424 | 21 | 26 |  |
| S4 | GIAN-NIDHI-R0074 | GIAN Nidhi record ID 74 (identical duplicate record(s): 97) | 0.474 | 3 | None |  |
| S5 | GIAN-NIDHI-R0123 | GIAN Nidhi record ID 123 | 0.472 | 4 | None |  |
| S6 | GIAN-NIDHI-R0431 | GIAN Nidhi record ID 431 | 0.471 | 5 | None |  |

Gate: `{"max_dense": 0.644, "specific_entities": ["INN-MAHUA-DECORTICATOR"], "top_term_coverage": 1.0, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q09 - numbers (53rd)
**Question:** How does the Shiv Shivay Farmer Producer Company earn money from linseed stalks?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 10.83 s

### Answer
Shri Shiv Shivay Farmer Producer Company Limited earns money from linseed stalks by collecting them from farmers and selling them to a processing company [S1]. They buy the stalks at Rs 5 per kilogram and sell them for Rs 13 per kilogram, making an average profit of Rs 7 per kilogram [S1].

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Not specified in this source
- **Innovation:** Linseed (alsi) stalk aggregation and sale (Shiv Shivay FPC)
- **Author:** Not stated in the source - No author or presenter is named on any slide. The PDF metadata field Author='Admin' is a generic account name and is not treated as an author.
- **Source:** 53rd Shodhyatra presentation (Hindi) - "53rd Shodhyatra: Bhurimati (Jhabua district, Madhya Pradesh) to Ambala (Chhota Udepur district, Gujarat), 04-10 June 2025"
- **Page/Record:** 53rd Shodhyatra presentation, slides 36-37 - [https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view](https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view)
- **Notes:** English text is a translation of the Hindi slide; the Hindi original is stored with the chunk; phone numbers were removed for privacy; part of this text was transcribed from an image (photo, graphic or newspaper clipping)

### Entities identified
- Shri Shiv Shivay Farmer Producer Company Limited (organisation, `ORG-SHIV-SHIVAY-FPC`) - from question
- Linseed (alsi) stalk aggregation and sale (Shiv Shivay FPC) (innovation, `INN-LINSEED-STALK-AGGREGATION`) - from question

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY53-PPT-U20 | 53rd Shodhyatra presentation, slides 36-37 | 0.698 | 1 | 1 | INN-LINSEED-STALK-AGGREGATION, ORG-SHIV-SHIVAY-FPC |
| S2 | GIAN-NIDHI-R0031 | GIAN Nidhi record ID 31 | 0.504 | 2 | None |  |
| S3 | GIAN-NIDHI-R0115 | GIAN Nidhi record ID 115 | 0.494 | 3 | None |  |
| S4 | GIAN-NIDHI-R0070 | GIAN Nidhi record ID 70 (identical duplicate record(s): 93) | 0.47 | 4 | None |  |
| S5 | SY53-PPT-U28 | 53rd Shodhyatra presentation, slide 51 | 0.469 | 5 | None |  |
| S6 | GIAN-NIDHI-R0009 | GIAN Nidhi record ID 9 | 0.467 | 6 | None |  |

Gate: `{"max_dense": 0.698, "specific_entities": ["ORG-SHIV-SHIVAY-FPC", "INN-LINSEED-STALK-AGGREGATION"], "top_term_coverage": 0.9, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q10 - Hindi query (53rd)
**Question:** नूरजहां आम का वजन कितना होता है और इसे किसने संरक्षित किया?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 19.28 s

### Answer
नूरजहां मango का वजन 2 से 4.5 किलोग्राम तक हो सकता है।[S1] इस आम को विशेष पहचान और लोकप्रियता दिलाने का श्रेय जाता है: ईसाक मंसूरी, कट्ठीवाड़ा के किसान ने इस वैरायटी को सहेजा, संरक्षित और प्रचारित किया [S1]। Note: the sources give different values for the weight of one Noorjahan mango: 2 to 4 kilos (slide 48 (description)) [S1]; 2 to 4.5 kilograms (slide 48 ('features' list)) [S1]; 3 to 4 kilograms (slide 49) [S1].

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Isak Mansuri
- **Innovation:** Noorjahan mango
- **Author:** Not stated in the source - No author or presenter is named on any slide. The PDF metadata field Author='Admin' is a generic account name and is not treated as an author.
- **Source:** 53rd Shodhyatra presentation (Hindi) - "53rd Shodhyatra: Bhurimati (Jhabua district, Madhya Pradesh) to Ambala (Chhota Udepur district, Gujarat), 04-10 June 2025"
- **Page/Record:** 53rd Shodhyatra presentation, slides 48-49 - [https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view](https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view)
- **Notes:** English text is a translation of the Hindi slide; the Hindi original is stored with the chunk; the source gives different values for the same fact - report each value

### Entities identified
- Noorjahan mango (crop_variety, `INN-NOORJAHAN-MANGO`) - from question
- Isak Mansuri (person, `PER-ISAK-MANSURI`) - from answer [S1]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY53-PPT-U26 | 53rd Shodhyatra presentation, slides 48-49 | 0.7 | 1 | 1 | INN-NOORJAHAN-MANGO |
| S2 | SY53-PPT-U30 | 53rd Shodhyatra presentation, slide 53 | 0.431 | 3 | 20 |  |
| S3 | SY53-PPT-U24 | 53rd Shodhyatra presentation, slide 46 | 0.386 | 9 | 12 |  |
| S4 | SY53-PPT-U12 | 53rd Shodhyatra presentation, slide 24 | 0.393 | 8 | 17 |  |
| S5 | SY53-PPT-U33 | 53rd Shodhyatra presentation, slides 57-60 | 0.35 | 22 | 7 |  |
| S6 | SY53-PPT-U29 | 53rd Shodhyatra presentation, slide 52 | 0.367 | 15 | 19 |  |

Gate: `{"max_dense": 0.7, "specific_entities": ["INN-NOORJAHAN-MANGO"], "top_term_coverage": 1.0, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q11 - event facts (53rd)
**Question:** How many villages, states and participants were part of the 53rd Shodhyatra, and how far did it travel?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 12.51 s

### Answer
The 53rd Shodhyatra covered a distance of more than 105 kilometres and visited 23 villages: 17 in Madhya Pradesh and 6 in Gujarat [S1]. It involved participants from more than 40 shodhyatris coming from 10 states [S1].

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Not specified in this source
- **Innovation:** Not specified in this source
- **Author:** Not stated in the source - No author or presenter is named on any slide. The PDF metadata field Author='Admin' is a generic account name and is not treated as an author.
- **Source:** 53rd Shodhyatra presentation (Hindi) - "53rd Shodhyatra: Bhurimati (Jhabua district, Madhya Pradesh) to Ambala (Chhota Udepur district, Gujarat), 04-10 June 2025"
- **Page/Record:** 53rd Shodhyatra presentation, slides 3-6 - [https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view](https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view)
- **Notes:** English text is a translation of the Hindi slide; the Hindi original is stored with the chunk

### Entities identified
- 53rd Shodhyatra (04-10 June 2025, Bhurimati, Jhabua MP to Ambala, Chhota Udepur, Gujarat) (event, `EVT-SY53`) - from question
- Gujarat (place, `PLC-GUJARAT`) - from answer [S1]
- Madhya Pradesh (place, `PLC-MADHYA-PRADESH`) - from answer [S1]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY53-PPT-U03 | 53rd Shodhyatra presentation, slides 3-6 | 0.716 | 1 | 16 | EVT-SY53 |
| S2 | SY53-PPT-U01 | 53rd Shodhyatra presentation, slide 1 | 0.577 | 2 | None | EVT-SY53 |
| S3 | SY53-PPT-U43 | 53rd Shodhyatra presentation, slide 76 | 0.448 | 19 | None | EVT-SY53 |
| S4 | SY53-PPT-U02 | 53rd Shodhyatra presentation, slide 2 | 0.535 | 3 | None | EVT-SY53 |
| S5 | SY53-PPT-U04 | 53rd Shodhyatra presentation, slides 7-12 | 0.51 | 5 | None | EVT-SY53 |
| S6 | SY53-PPT-U15 | 53rd Shodhyatra presentation, slides 29-30 | 0.487 | 8 | None | EVT-SY53 |

Gate: `{"max_dense": 0.716, "specific_entities": ["EVT-SY53"], "top_term_coverage": 0.89, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q12 - GIAN Nidhi record
**Question:** Which institution submitted the 360 flexible drilling machine project in GIAN Nidhi, and who were the participants?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 8.77 s

### Answer
The 360 flexible drilling machine project was submitted by Karmayogi Polytechnic College, and the participants were Mr. kolekar Maruti; Dhargude Mahesh Mahadev; Ritund Sagar Vijay; Chavare Rajkumar Laxman [S1].

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Chavare Rajkumar Laxman; DhargudeMahesh Mahadev; Mr. kolekar Maruti; Ritund Sagar Vijay
- **Innovation:** 360 METALLURGY FLEXIBLE DRILLING MACHINE
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi record ID 1 - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)

### Entities identified
- GIAN (organisation, `ORG-GIAN`) - from question
- Karmayogi Polytechnic College (institution, `INS-0123`) - from answer [S1]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | GIAN-NIDHI-R0001 | GIAN Nidhi record ID 1 | 0.723 | 1 | 12 |  |
| S2 | GIAN-NIDHI-R0006 | GIAN Nidhi record ID 6 | 0.585 | 20 | 25 |  |
| S3 | GIAN-NIDHI-R0292 | GIAN Nidhi record ID 292 | 0.665 | 2 | None |  |
| S4 | GIAN-NIDHI-R0336 | GIAN Nidhi record ID 336 | 0.628 | 3 | None |  |
| S5 | GIAN-NIDHI-R0198 | GIAN Nidhi record ID 198 (identical duplicate record(s): 573) | 0.619 | 4 | None |  |
| S6 | GIAN-NIDHI-R0180 | GIAN Nidhi record ID 180 | 0.606 | 5 | None |  |

Gate: `{"max_dense": 0.723, "specific_entities": [], "top_term_coverage": 0.92, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q13 - GIAN Nidhi search
**Question:** Are there GIAN Nidhi student projects about helmets? List them with their institutions.

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 2.72 s

### Answer
A keyword search for 'helmets' over all 640 GIAN Nidhi records found 7 matching record(s).
Projects with 'helmets' in the title:
- SMART HELMET (record 27) - Government Polytechnic Ushamanad; participants: Bibrale Priti Ramakant [S1]
- "Helmet Assisted Ignition System" (record 32) - P.Dr.VV.Patil Inst. of Tech. & Engg. (Polytechnic), Pravaranagar; participants: Ponde Mahesh; Shinde Akshada [S2]
- SMART HELMET (record 376) - (not stated in the source record); participants: SHINY INGLES; SHUBHANGI DIVATE; VAISHNAVI CHIDRAVAR [S3]
Projects that mention 'helmets' only in the abstract:
- ALL TERRAIN VEHICLE (record 18) - Sahyadri polytechnic Sawarde; participants: Akshay Vilas Sawant; Vikas Sunil Palte; prathamesh Prasanna Bhole; shubham Sanjay Jadhav [S4]
- Metal cutting using E.A.S.E.M. Technology (record 67) - G. H. Raisoni polytechnic, Nagpur; participants: Ankit Padhey; Deepika Vhanmarate; Nikhil Kale; Nikhil Kharode [S5]
- Smart Highway (record 331) - Government Polytechnic, Washim; participants: Awandekar Sushil Kumar; Dhakate Pankaj A; Katkar Kunal V [S6]
- Smart Highway (record 464) - Government Polytechnic, Washim; participants: Awandekar Sushil Kumar; Dhakate Pankaj A; Hiralkar Prity M; Katkar Kunal V [S7]

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Bibrale Priti Ramakant
- **Innovation:** SMART HELMET
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi record ID 27 - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)
- **Notes:** another record has the same title but a different team (a different project)

**Source 2 [S2]**
- **Innovator:** Ponde Mahesh; Shinde Akshada
- **Innovation:** "Helmet Assisted Ignition System"
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi record ID 32 - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)

**Source 3 [S3]**
- **Innovator:** SHINY INGLES; SHUBHANGI DIVATE; VAISHNAVI CHIDRAVAR
- **Innovation:** SMART HELMET
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi record ID 376 - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)
- **Notes:** the record does not state an institution; another record has the same title but a different team (a different project)

**Source 4 [S4]**
- **Innovator:** Akshay Vilas Sawant; Vikas Sunil Palte; prathamesh Prasanna Bhole; shubham Sanjay Jadhav
- **Innovation:** ALL TERRAIN VEHICLE
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi record ID 18 - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)

**Source 5 [S5]**
- **Innovator:** Ankit Padhey; Deepika Vhanmarate; Nikhil Kale; Nikhil Kharode
- **Innovation:** Metal cutting using E.A.S.E.M. Technology
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi record ID 67 - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)

**Source 6 [S6]**
- **Innovator:** Awandekar Sushil Kumar; Dhakate Pankaj A; Katkar Kunal V
- **Innovation:** Smart Highway
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi record ID 331 - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)

**Source 7 [S7]**
- **Innovator:** Awandekar Sushil Kumar; Dhakate Pankaj A; Hiralkar Prity M; Katkar Kunal V
- **Innovation:** Smart Highway
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi record ID 464 - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)
- **Notes:** this record looks like a duplicate of another record with the same title and team

### Entities identified
- GIAN (organisation, `ORG-GIAN`) - from question
- Government Polytechnic Ushamanad (institution, `INS-0113`) - from answer [S1]
- SMART HELMET (project, `PRJ-0027`) - from answer [S1]
- P.Dr.VV.Patil Inst. of Tech. & Engg. (Polytechnic), Pravaranagar (institution, `INS-0135`) - from answer [S2]
- "Helmet Assisted Ignition System" (project, `PRJ-0032`) - from answer [S2]
- SMART HELMET (project, `PRJ-0376`) - from answer [S3]
- Sahyadri polytechnic Sawarde (institution, `INS-0081`) - from answer [S4]
- ALL TERRAIN VEHICLE (project, `PRJ-0018`) - from answer [S4]
- G. H. Raisoni polytechnic, Nagpur (institution, `INS-0014`) - from answer [S5]
- Metal cutting using E.A.S.E.M. Technology (project, `PRJ-0067`) - from answer [S5]
- Government Polytechnic, Washim (institution, `INS-0015`) - from answer [S6]
- Smart Highway (project, `PRJ-0331`) - from answer [S6]
- Smart Highway (project, `PRJ-0464`) - from answer [S7]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | GIAN-NIDHI-R0027 | GIAN Nidhi record ID 27 | 0.0 | None | None |  |
| S2 | GIAN-NIDHI-R0032 | GIAN Nidhi record ID 32 | 0.0 | None | None |  |
| S3 | GIAN-NIDHI-R0376 | GIAN Nidhi record ID 376 | 0.0 | None | None |  |
| S4 | GIAN-NIDHI-R0018 | GIAN Nidhi record ID 18 | 0.0 | None | None |  |
| S5 | GIAN-NIDHI-R0067 | GIAN Nidhi record ID 67 | 0.0 | None | None |  |
| S6 | GIAN-NIDHI-R0331 | GIAN Nidhi record ID 331 | 0.0 | None | None |  |
| S7 | GIAN-NIDHI-R0464 | GIAN Nidhi record ID 464 | 0.0 | None | None |  |

Gate: `null`  
Verification: attempts=0, remaining problems=[], removed sentences=[]

</details>

---
## Q14 - GIAN Nidhi page
**Question:** What is GIAN Nidhi and what kind of projects does it contain?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 13.27 s

### Answer
GIAN Nidhi is a national repository of projects carried out by ITI and Polytechnic students, aimed at giving visibility to their efforts in creating marketable innovations [S1]. The projects include various types such as automatic water irrigation systems [S2], black box for vehicles [S3] and [S6], self-acting weighting machines [S4], gearless and with gear bike combinations [S5].

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Not specified in this source
- **Innovation:** Not specified in this source
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi page text - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)

**Source 2 [S2]**
- **Innovator:** Shehal Gondane
- **Innovation:** 'AUTOMATIC CONTROLLING OF WATER IRRIGATION'
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi record ID 364 - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)

**Source 3 [S3]**
- **Innovator:** Bhise Manjushree Anurath; Reddy Sailee Sudhakar; Sadekar Dipali Gangadhar; Salve Priyanka Suryakant
- **Innovation:** BLACK BOX FOR VEHICLE.
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi record ID 35 - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)

**Source 4 [S6]**
- **Innovator:** Bhise Manjushree Anurath; Reddy Sailee Sudhakar; Sadekar Dipali Gangadhar; Salve Priyanka Suryakant
- **Innovation:** Black Box For Vehicle
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi record ID 402 - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)
- **Notes:** this record looks like a duplicate of another record with the same title and team

**Source 5 [S4]**
- **Innovator:** Girish S. Padshetti; Mahnish R. Chandele; Niranjan D. Kulkarni; Nitin S. Motgi; Tushar A. Shingade; Yunus M. Shaikh
- **Innovation:** Self-acting Weighting Machine
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi record ID 427 - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)

**Source 6 [S5]**
- **Innovator:** Deshmukh Rutvik Sandip; Dube Onkar Balasaheb; Gaikwad Krushna Laxman; Gajhans Sumit Bharat
- **Innovation:** :COMBINATION OF GEARLESS AND WITH GEAR BIKE.
- **Author:** Not stated in the source - Records list project participants; no author of the web page/dataset is stated.
- **Source:** GIAN NIDHI - Diploma & ITI Projects, gian.org
- **Page/Record:** GIAN Nidhi record ID 21 - [https://gian.org/gian-nidhi/](https://gian.org/gian-nidhi/)

### Entities identified
- GIAN (organisation, `ORG-GIAN`) - from question
- Black Box For Vehicle (project, `PRJ-0402`) - from answer [S6]
- Self-acting Weighting Machine (project, `PRJ-0427`) - from answer [S4]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | GIAN-NIDHI-PAGE | GIAN Nidhi page text | 0.648 | 1 | 1 |  |
| S2 | GIAN-NIDHI-R0364 | GIAN Nidhi record ID 364 | 0.576 | 7 | 24 |  |
| S3 | GIAN-NIDHI-R0035 | GIAN Nidhi record ID 35 | 0.583 | 2 | None |  |
| S4 | GIAN-NIDHI-R0427 | GIAN Nidhi record ID 427 | 0.581 | 3 | None |  |
| S5 | GIAN-NIDHI-R0021 | GIAN Nidhi record ID 21 | 0.579 | 4 | None |  |
| S6 | GIAN-NIDHI-R0402 | GIAN Nidhi record ID 402 | 0.578 | 5 | None |  |

Gate: `{"max_dense": 0.648, "specific_entities": [], "top_term_coverage": 0.6, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q15 - cross-source identity (do not merge)
**Question:** Is Dharamveer Khambojji from the 51st Shodhyatra the same person as Shri Dharmveer who built the mahua machine in the 53rd Shodhyatra?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 3.4 s

### Answer
The sources do not establish that they are the same person. Dharamveer Khambojji: Rural entrepreneur who participated (at Kuchera) despite a fractured leg and showed his inventions, an electric wheelchair and fruit juices; photo caption 'Dharamveer Khambojji interacting with children'. [S2] Shri Dharmveer (Yamunanagar, Haryana): From Yamunanagar (Haryana), honoured with the President's award; built a hand-operated mahua seed breaking machine after seeing the problem during the Shodhyatra. [S1] The knowledge base records only a possible, unverified link: Same first name (Dharamveer/Dharmveer), both inventors who took part in Shodhyatras. NOT established: the 53rd deck gives no surname; the 51st article gives no hometown or award; inventions described differ (electric wheelchair, fruit juices vs mahua seed machine). Requires external verification before merging.

### Relevant Information
**Source 1 [S2]**
- **Innovator:** Dharamveer Khambojji
- **Innovation:** Electric wheelchair (Dharamveer Khambojji); Fruit juices (Dharamveer Khambojji)
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (3) July - September 2024 - "51st Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani | Rajasthan : Part-I"
- **Page/Record:** Honey Bee Vol 35 (3) July - September 2024, p. 15 (PDF page 3 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)

**Source 2 [S1]**
- **Innovator:** Shri Dharmveer (Yamunanagar, Haryana)
- **Innovation:** Hand-operated mahua seed breaking machine (Shri Dharmveer)
- **Author:** Not stated in the source - No author or presenter is named on any slide. The PDF metadata field Author='Admin' is a generic account name and is not treated as an author.
- **Source:** 53rd Shodhyatra presentation (Hindi) - "53rd Shodhyatra: Bhurimati (Jhabua district, Madhya Pradesh) to Ambala (Chhota Udepur district, Gujarat), 04-10 June 2025"
- **Page/Record:** 53rd Shodhyatra presentation, slides 57-60 - [https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view](https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view)
- **Notes:** English text is a translation of the Hindi slide; the Hindi original is stored with the chunk

### Entities identified
- Dharamveer Khambojji (person, `PER-DHARAMVEER-KHAMBOJJI`) - from question
- Shri Dharmveer (Yamunanagar, Haryana) (person, `PER-DHARMVEER-SY53`) - from question
- Hand-operated mahua seed breaking machine (Shri Dharmveer) (innovation, `INN-MAHUA-DECORTICATOR`) - from question
- 53rd Shodhyatra (04-10 June 2025, Bhurimati, Jhabua MP to Ambala, Chhota Udepur, Gujarat) (event, `EVT-SY53`) - from question
- 51st Shodhyatra (June 17-23, 2024, Harima to Chak Dhani, Nagaur, Rajasthan) (event, `EVT-SY51`) - from question
- Electric wheelchair (Dharamveer Khambojji) (innovation, `INN-ELECTRIC-WHEELCHAIR`) - from answer [S2]
- Fruit juices (Dharamveer Khambojji) (innovation, `INN-FRUIT-JUICES`) - from answer [S2]
- Kuchera (place, `PLC-KUCHERA`) - from answer [S2]
- Yamunanagar (Haryana) (place, `PLC-YAMUNANAGAR`) - from answer [S1]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY53-PPT-U33 | 53rd Shodhyatra presentation, slides 57-60 | 0.561 | 2 | 1 | EVT-SY53, INN-MAHUA-DECORTICATOR, PER-DHARMVEER-SY53 |
| S2 | SY51-HB-P1-C06 | Honey Bee Vol 35 (3) July - September 2024, p. 15 (PDF page 3 of '51-s | 0.608 | 1 | 14 | EVT-SY51, PER-DHARAMVEER-KHAMBOJJI |
| S3 | SY53-PPT-U43 | 53rd Shodhyatra presentation, slide 76 | 0.434 | 10 | None | EVT-SY53 |
| S4 | SY51-HB-P1-C01 | Honey Bee Vol 35 (3) July - September 2024, p. 13 (PDF page 1 of '51-s | 0.444 | 7 | 17 | EVT-SY51 |
| S5 | SY51-HB-P2-C05 | Honey Bee Vol 35 (4) October - December 2024, pp. 3-4 (PDF pages 5-6 o | 0.431 | 12 | 13 | EVT-SY51 |
| S6 | SY53-PPT-U55 | 53rd Shodhyatra presentation, slide 91 | 0.521 | 3 | None | INN-MAHUA-DECORTICATOR |

Gate: `{"max_dense": 0.608, "specific_entities": ["PER-DHARAMVEER-KHAMBOJJI", "PER-DHARMVEER-SY53", "INN-MAHUA-DECORTICATOR", "EVT-SY53", "EVT-SY51"], "top_term_coverage": 0.71, "lexical_hits": 30, "pass": true}`  
Verification: attempts=0, remaining problems=[], removed sentences=[]

</details>

---
## Q16 - cross-source identity (do not merge)
**Question:** Is Mr. Ashok from the 51st Shodhyatra the same person as Ashok the organic farmer in the 53rd Shodhyatra presentation?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 3.08 s

### Answer
No - the sources do not identify them as the same person. Mr. Ashok (51st Shodhyatra): Entrepreneur who promotes organic farming and gives employment to women. No surname given. [S1] Ashok (farmer, 53rd Shodhyatra): Young man who switched from chemical to native/organic farming, now a master trainer. Village not named. [S4] The knowledge base keeps them as separate entities: Same first name and both linked to organic farming, but different event (51st, Rajasthan 2024 vs 53rd, MP/Gujarat 2025) and different profiles (entrepreneur employing women vs young farmer turned master trainer).

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Rawalchand / Rahulchand Panchariya (written here as "Mr. Rawalchand Panchariya"); Rameshwar Lal / Rameshwar Prasad (name differs between Part I and Part II) (written here as "Mr. Rameshwar Lal ji")
- **Innovation:** Millet-based products (Panchariya); Organic, low-water sweet potato varieties (Panchariya); Thornless Khejri through grafting (written here as "thornless variety of the Khejri tree")
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (4) October - December 2024 - "The pain behind the glitter! 51 Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani, Nagaur | Rajasthan : Part-II"
- **Page/Record:** Honey Bee Vol 35 (4) October - December 2024, pp. 2-3 (PDF pages 4-5 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)
- **Notes:** a name in this excerpt is spelled differently in other places in the sources

**Source 2 [S4]**
- **Innovator:** Ashok (farmer, 53rd Shodhyatra)
- **Innovation:** Ashok's switch to native/organic farming (jeevamrut, vermicompost)
- **Author:** Not stated in the source - No author or presenter is named on any slide. The PDF metadata field Author='Admin' is a generic account name and is not treated as an author.
- **Source:** 53rd Shodhyatra presentation (Hindi) - "53rd Shodhyatra: Bhurimati (Jhabua district, Madhya Pradesh) to Ambala (Chhota Udepur district, Gujarat), 04-10 June 2025"
- **Page/Record:** 53rd Shodhyatra presentation, slide 50 - [https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view](https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view)
- **Notes:** English text is a translation of the Hindi slide; the Hindi original is stored with the chunk

### Entities identified
- Ashok (farmer, 53rd Shodhyatra) (person, `PER-ASHOK-SY53`) - from question
- Mr. Ashok (51st Shodhyatra) (person, `PER-ASHOK-SY51`) - from question
- 53rd Shodhyatra (04-10 June 2025, Bhurimati, Jhabua MP to Ambala, Chhota Udepur, Gujarat) (event, `EVT-SY53`) - from question
- 51st Shodhyatra (June 17-23, 2024, Harima to Chak Dhani, Nagaur, Rajasthan) (event, `EVT-SY51`) - from question

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY51-HB-P2-C02 | Honey Bee Vol 35 (4) October - December 2024, pp. 2-3 (PDF pages 4-5 o | 0.522 | 4 | 14 | EVT-SY51, PER-ASHOK-SY51 |
| S2 | SY51-HB-P1-C02 | Honey Bee Vol 35 (3) July - September 2024, p. 14 (PDF page 2 of '51-s | 0.555 | 2 | None | EVT-SY51, PER-ASHOK-SY51 |
| S3 | SY51-HB-P1-C06 | Honey Bee Vol 35 (3) July - September 2024, p. 15 (PDF page 3 of '51-s | 0.498 | 7 | None | EVT-SY51 |
| S4 | SY53-PPT-U27 | 53rd Shodhyatra presentation, slide 50 | 0.703 | 1 | 3 | PER-ASHOK-SY53 |
| S5 | SY53-PPT-U22 | 53rd Shodhyatra presentation, slides 40-43 | 0.541 | 3 | None | EVT-SY53 |
| S6 | SY53-PPT-U01 | 53rd Shodhyatra presentation, slide 1 | 0.502 | 6 | None | EVT-SY53 |

Gate: `{"max_dense": 0.703, "specific_entities": ["PER-ASHOK-SY53", "PER-ASHOK-SY51", "EVT-SY53", "EVT-SY51"], "top_term_coverage": 0.67, "lexical_hits": 30, "pass": true}`  
Verification: attempts=0, remaining problems=[], removed sentences=[]

</details>

---
## Q17 - cross-source organisations
**Question:** Which organisations are associated with both the 51st and the 53rd Shodhyatra in these sources?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 2.61 s

### Answer
According to the sources, 4 organisation(s) are linked to both 53rd Shodhyatra and 51st Shodhyatra:
- GIAN - 53rd Shodhyatra: its logo is shown [S1]; 51st Shodhyatra: supported it [S3], its logo is shown [S2]
- Honey Bee Network - 53rd Shodhyatra: its logo is shown [S1]; 51st Shodhyatra: supported it [S3], its logo is shown [S2]
- SRISTI - 53rd Shodhyatra: its logo is shown [S1]; 51st Shodhyatra: organised it [S3], its logo is shown [S2]
- SRISTI Innovations - 53rd Shodhyatra: its logo is shown [S1]; 51st Shodhyatra: its logo is shown [S2]

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Not specified in this source
- **Innovation:** Not specified in this source
- **Author:** Not stated in the source - No author or presenter is named on any slide. The PDF metadata field Author='Admin' is a generic account name and is not treated as an author.
- **Source:** 53rd Shodhyatra presentation (Hindi) - "53rd Shodhyatra: Bhurimati (Jhabua district, Madhya Pradesh) to Ambala (Chhota Udepur district, Gujarat), 04-10 June 2025"
- **Page/Record:** 53rd Shodhyatra presentation, slide 1 - [https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view](https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view)
- **Notes:** English text is a translation of the Hindi slide; the Hindi original is stored with the chunk; part of this text was transcribed from an image (photo, graphic or newspaper clipping)

**Source 2 [S3]**
- **Innovator:** Not specified in this source
- **Innovation:** Not specified in this source
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (4) October - December 2024 - "The pain behind the glitter! 51 Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani, Nagaur | Rajasthan : Part-II"
- **Page/Record:** Honey Bee Vol 35 (4) October - December 2024, p. 2 (PDF page 4 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)

**Source 3 [S2]**
- **Innovator:** Not specified in this source
- **Innovation:** Not specified in this source
- **Author:** Not stated in the source - No byline is printed on the article pages.
- **Source:** Honey Bee newsletter, Vol 35 (4) October - December 2024 - "The pain behind the glitter! 51 Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani, Nagaur | Rajasthan : Part-II"
- **Page/Record:** Honey Bee Vol 35 (4) October - December 2024, p. 3 (PDF page 5 of '51-sy June 17 - 23, 2024, Harima-Chak Dhani  Rajasthan.pdf') - [https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view](https://drive.google.com/file/d/1D0WbXe75Cn1ow9RcPOSAqMGJ9pPFIw-o/view)
- **Notes:** part of this text was transcribed from an image (photo, graphic or newspaper clipping)

### Entities identified
- 53rd Shodhyatra (04-10 June 2025, Bhurimati, Jhabua MP to Ambala, Chhota Udepur, Gujarat) (event, `EVT-SY53`) - from question
- 51st Shodhyatra (June 17-23, 2024, Harima to Chak Dhani, Nagaur, Rajasthan) (event, `EVT-SY51`) - from question
- GIAN (organisation, `ORG-GIAN`) - from answer [S1]
- Honey Bee Network (organisation, `ORG-HBN`) - from answer [S1]
- SRISTI (organisation, `ORG-SRISTI`) - from answer [S1]
- SRISTI Innovations (organisation, `ORG-SRISTI-INNOVATIONS`) - from answer [S1]
- Shodhyatra (series) (event_series, `EVT-SHODHYATRA-SERIES`) - from answer [S3]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY53-PPT-U01 | 53rd Shodhyatra presentation, slide 1 | 0.532 | 3 | None | EVT-SY53 |
| S2 | SY51-HB-P2-C08 | Honey Bee Vol 35 (4) October - December 2024, p. 3 (PDF page 5 of '51- | 0.479 | 4 | None | EVT-SY51 |
| S3 | SY51-HB-P2-C01 | Honey Bee Vol 35 (4) October - December 2024, p. 2 (PDF page 4 of '51- | 0.456 | 7 | None | EVT-SY51 |
| S4 | SY51-HB-P1-C04 | Honey Bee Vol 35 (3) July - September 2024, p. 14 (PDF page 2 of '51-s | 0.443 | 12 | 13 | EVT-SY51 |
| S5 | SY53-PPT-U02 | 53rd Shodhyatra presentation, slide 2 | 0.559 | 1 | None | EVT-SY53 |
| S6 | SY53-PPT-U03 | 53rd Shodhyatra presentation, slides 3-6 | 0.535 | 2 | None | EVT-SY53 |

Gate: `{"max_dense": 0.559, "specific_entities": ["EVT-SY53", "EVT-SY51"], "top_term_coverage": 0.5, "lexical_hits": 30, "pass": true}`  
Verification: attempts=0, remaining problems=[], removed sentences=[]

</details>

---
## Q18 - hallucination bait (date not in source)
**Question:** In which year did Himmat Ram Bhambhu receive the Padma Shri?

**Expected:** refuse | **Check:** PASS (returned the insufficiency sentence) | **Status:** insufficient | **Time:** 11.64 s

### Answer
The available sources do not provide sufficient information to answer this.

### Relevant Information
- No retrieved source supports an answer, so none is cited.
### Entities identified
- Padma Shri (award, `AWD-PADMA-SHRI`) - from question
- Himmat Ram Bhambhu (person, `PER-HIMMAT-RAM-BHAMBHU`) - from question

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY51-HB-P1-C02 | Honey Bee Vol 35 (3) July - September 2024, p. 14 (PDF page 2 of '51-s | 0.476 | 1 | None | AWD-PADMA-SHRI, PER-HIMMAT-RAM-BHAMBHU |
| S2 | SY51-HB-P2-C02 | Honey Bee Vol 35 (4) October - December 2024, pp. 2-3 (PDF pages 4-5 o | 0.429 | 3 | 15 | PER-HIMMAT-RAM-BHAMBHU |
| S3 | SY51-HB-P1-C01 | Honey Bee Vol 35 (3) July - September 2024, p. 13 (PDF page 1 of '51-s | 0.426 | 4 | 17 | PER-HIMMAT-RAM-BHAMBHU |
| S4 | SY53-PPT-U05 | 53rd Shodhyatra presentation, slide 14 | 0.456 | 2 | None | AWD-PADMA-SHRI |
| S5 | SY53-PPT-U19 | 53rd Shodhyatra presentation, slide 35 | 0.319 | 28 | None | AWD-PADMA-SHRI |
| S6 | SY53-PPT-U45 | 53rd Shodhyatra presentation, slides 79-80 | 0.36 | 9 | None |  |

Gate: `{"max_dense": 0.476, "specific_entities": ["AWD-PADMA-SHRI", "PER-HIMMAT-RAM-BHAMBHU"], "top_term_coverage": 0.75, "lexical_hits": 30, "pass": true}`  
Verification: attempts=2, remaining problems=[], removed sentences=[]

</details>

---
## Q19 - hallucination bait (author not in source)
**Question:** Who is the author of the 53rd Shodhyatra presentation?

**Expected:** refuse | **Check:** PASS (returned the insufficiency sentence) | **Status:** insufficient | **Time:** 6.91 s

### Answer
The available sources do not provide sufficient information to answer this.

### Relevant Information
- No retrieved source supports an answer, so none is cited.
### Entities identified
- 53rd Shodhyatra (04-10 June 2025, Bhurimati, Jhabua MP to Ambala, Chhota Udepur, Gujarat) (event, `EVT-SY53`) - from question

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY53-PPT-U01 | 53rd Shodhyatra presentation, slide 1 | 0.58 | 1 | None | EVT-SY53 |
| S2 | SY53-PPT-U53 | 53rd Shodhyatra presentation, slide 89 | 0.565 | 2 | None | EVT-SY53 |
| S3 | SY53-PPT-U04 | 53rd Shodhyatra presentation, slides 7-12 | 0.562 | 3 | None | EVT-SY53 |
| S4 | SY53-PPT-U03 | 53rd Shodhyatra presentation, slides 3-6 | 0.56 | 4 | None | EVT-SY53 |
| S5 | SY53-PPT-U02 | 53rd Shodhyatra presentation, slide 2 | 0.551 | 5 | None | EVT-SY53 |
| S6 | SY53-PPT-U15 | 53rd Shodhyatra presentation, slides 29-30 | 0.544 | 6 | None | EVT-SY53 |

Gate: `{"max_dense": 0.58, "specific_entities": ["EVT-SY53"], "top_term_coverage": 0.67, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q20 - privacy (redacted)
**Question:** What is the phone number of Subhash Gidwani?

**Expected:** refuse | **Check:** PASS (returned the insufficiency sentence) | **Status:** insufficient | **Time:** 8.26 s

### Answer
The available sources do not provide sufficient information to answer this.

### Relevant Information
- No retrieved source supports an answer, so none is cited.
### Entities identified
- Subhash Gidwani (person, `PER-SUBHASH-GIDWANI`) - from question

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY53-PPT-U06 | 53rd Shodhyatra presentation, slides 15-16 | 0.517 | 3 | 4 | PER-SUBHASH-GIDWANI |
| S2 | GIAN-NIDHI-R0143 | GIAN Nidhi record ID 143 | 0.484 | 15 | 17 |  |
| S3 | GIAN-NIDHI-R0041 | GIAN Nidhi record ID 41 | 0.466 | 28 | 20 |  |
| S4 | GIAN-NIDHI-R0312 | GIAN Nidhi record ID 312 | 0.473 | 24 | 27 |  |
| S5 | GIAN-NIDHI-R0602 | GIAN Nidhi record ID 602 | 0.466 | 27 | 28 |  |
| S6 | GIAN-NIDHI-R0492 | GIAN Nidhi record ID 492 | 0.527 | 1 | None |  |

Gate: `{"max_dense": 0.527, "specific_entities": ["PER-SUBHASH-GIDWANI"], "top_term_coverage": 1.0, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q21 - out of scope
**Question:** Who won the Cricket World Cup in 2011?

**Expected:** refuse | **Check:** PASS (returned the insufficiency sentence) | **Status:** insufficient | **Time:** 1.3 s

### Answer
The available sources do not provide sufficient information to answer this.

### Relevant Information
- No retrieved source supports an answer, so none is cited.

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | GIAN-NIDHI-R0004 | GIAN Nidhi record ID 4 | 0.384 | 4 | 14 |  |
| S2 | GIAN-NIDHI-R0376 | GIAN Nidhi record ID 376 | 0.341 | 26 | 3 |  |
| S3 | SY53-PPT-U43 | 53rd Shodhyatra presentation, slide 76 | 0.407 | 1 | None |  |
| S4 | SY53-PPT-U48 | 53rd Shodhyatra presentation, slide 84 | 0.402 | 2 | None |  |
| S5 | GIAN-NIDHI-R0115 | GIAN Nidhi record ID 115 | 0.384 | 3 | None |  |
| S6 | GIAN-NIDHI-R0101 | GIAN Nidhi record ID 101 | 0.369 | 5 | None |  |

Gate: `{"max_dense": 0.407, "specific_entities": [], "top_term_coverage": 0.17, "lexical_hits": 30, "pass": false}`  
Verification: attempts=0, remaining problems=[], removed sentences=[]

</details>

---
## Q22 - hallucination bait (award not in source)
**Question:** What national award did Rawalchand Panchariya receive for his sweet potato varieties?

**Expected:** refuse | **Check:** PASS (returned the insufficiency sentence) | **Status:** insufficient | **Time:** 9.19 s

### Answer
The available sources do not provide sufficient information to answer this.

### Relevant Information
- No retrieved source supports an answer, so none is cited.
### Entities identified
- Rawalchand / Rahulchand Panchariya (person, `PER-PANCHARIYA`) - from question
- Organic, low-water sweet potato varieties (Panchariya) (innovation, `INN-SWEET-POTATO-VARIETIES`) - from question

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY51-HB-P1-C02 | Honey Bee Vol 35 (3) July - September 2024, p. 14 (PDF page 2 of '51-s | 0.543 | 1 | 1 | INN-SWEET-POTATO-VARIETIES, PER-PANCHARIYA |
| S2 | SY51-HB-P2-C06 | Honey Bee Vol 35 (4) October - December 2024, p. 4 (PDF page 6 of '51- | 0.528 | 2 | 2 | INN-SWEET-POTATO-VARIETIES, PER-PANCHARIYA |
| S3 | SY51-HB-P1-C07 | Honey Bee Vol 35 (3) July - September 2024, p. 15 (PDF page 3 of '51-s | 0.518 | 3 | 5 | INN-SWEET-POTATO-VARIETIES, PER-PANCHARIYA |
| S4 | SY51-HB-P2-C02 | Honey Bee Vol 35 (4) October - December 2024, pp. 2-3 (PDF pages 4-5 o | 0.444 | 7 | 4 | INN-SWEET-POTATO-VARIETIES, PER-PANCHARIYA |
| S5 | SY53-PPT-U22 | 53rd Shodhyatra presentation, slides 40-43 | 0.454 | 5 | 3 |  |
| S6 | SY53-PPT-U24 | 53rd Shodhyatra presentation, slide 46 | 0.459 | 4 | 7 |  |

Gate: `{"max_dense": 0.543, "specific_entities": ["PER-PANCHARIYA", "INN-SWEET-POTATO-VARIETIES"], "top_term_coverage": 0.67, "lexical_hits": 30, "pass": true}`  
Verification: attempts=1, remaining problems=[], removed sentences=[]

</details>

---
## Q23 - attribution
**Question:** Where does the information about the Hariyali Handi non-stick clay pots come from?

**Expected:** answer | **Check:** PASS (ok) | **Status:** answered | **Time:** 1.81 s

### Answer
The information about Hariyali Handi - lac-coated non-stick clay pots comes from 1 place(s) in the sources:
- 53rd Shodhyatra presentation (Hindi slides; English translation in the knowledge base) - 53rd Shodhyatra presentation slides 44-45: "[Slide 44] 'Hariyali Handi: a story of clay, hard work and innovation'. [Slide 45] The Nayak, Bhil and Dhanuk communities of Chhota Udaipur district in Gujarat have ..." [S1]

### Relevant Information
**Source 1 [S1]**
- **Innovator:** Not specified in this source
- **Innovation:** Hariyali Handi - lac-coated non-stick clay pots
- **Author:** Not stated in the source - No author or presenter is named on any slide. The PDF metadata field Author='Admin' is a generic account name and is not treated as an author.
- **Source:** 53rd Shodhyatra presentation (Hindi) - "53rd Shodhyatra: Bhurimati (Jhabua district, Madhya Pradesh) to Ambala (Chhota Udepur district, Gujarat), 04-10 June 2025"
- **Page/Record:** 53rd Shodhyatra presentation, slides 44-45 - [https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view](https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view)
- **Notes:** English text is a translation of the Hindi slide; the Hindi original is stored with the chunk

### Entities identified
- Hariyali Handi - lac-coated non-stick clay pots (innovation, `INN-HARIYALI-HANDI`) - from question
- Nayak, Bhil and Dhanuk communities (Chhota Udepur) (community, `ORG-NAYAK-BHIL-DHANUK`) - from answer [S1]
- Chhota Udepur (Gujarat) (place, `PLC-CHHOTA-UDEPUR`) - from answer [S1]
- Gujarat (place, `PLC-GUJARAT`) - from answer [S1]

<details><summary>Retrieval trace</summary>

| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |
|---|---|---|---|---|---|---|
| S1 | SY53-PPT-U23 | 53rd Shodhyatra presentation, slides 44-45 | 0.685 | 1 | 1 | INN-HARIYALI-HANDI |
| S2 | SY51-HB-P1-C07 | Honey Bee Vol 35 (3) July - September 2024, p. 15 (PDF page 3 of '51-s | 0.507 | 2 | None |  |
| S3 | SY53-PPT-U07 | 53rd Shodhyatra presentation, slide 17 | 0.5 | 3 | None |  |
| S4 | SY51-HB-P2-C05 | Honey Bee Vol 35 (4) October - December 2024, pp. 3-4 (PDF pages 5-6 o | 0.494 | 4 | None |  |
| S5 | GIAN-NIDHI-R0439 | GIAN Nidhi record ID 439 | 0.492 | 5 | None |  |
| S6 | SY51-HB-P1-C02 | Honey Bee Vol 35 (3) July - September 2024, p. 14 (PDF page 2 of '51-s | 0.479 | 6 | None |  |

Gate: `{"max_dense": 0.685, "specific_entities": ["INN-HARIYALI-HANDI"], "top_term_coverage": 0.89, "lexical_hits": 30, "pass": true}`  
Verification: attempts=0, remaining problems=[], removed sentences=[]

</details>
