# Quy trinh xu ly Public Phase

Public phase dung bo 120 cau hoi cong khai de kiem tra va toi uu solution truoc
private phase.

## 1. Chuan bi

Can co:

```text
.env
solution/config.json
solution/prompt.txt
solution/wrapper.py
solution/findings.json
bin/public/observathon-sim/observathon-sim
bin/public/observathon-score/observathon-score
```

File `.env` phai chua API key hop le:

```text
OPENAI_API_KEY=...
```

Chay self-check:

```powershell
python harness\selfcheck.py
```

## 2. Chay Public Simulator

Luon tao file co ten rieng de khong ghi de ket qua tot:

```powershell
docker run --rm `
  --env-file .env `
  -v "${PWD}:/lab" `
  -w /lab `
  python:3.12-slim `
  bash -c "chmod +x bin/public/observathon-sim/observathon-sim && ./bin/public/observathon-sim/observathon-sim --config solution/config.json --wrapper solution/wrapper.py --out public_run_candidate.json --concurrency 8"
```

## 3. Cham Public Score

```powershell
docker run --rm `
  -v "${PWD}:/lab" `
  -w /lab `
  python:3.12-slim `
  bash -c "chmod +x bin/public/observathon-score/observathon-score && ./bin/public/observathon-score/observathon-score --run public_run_candidate.json --findings solution/findings.json --team NguyenThiYen --out public_score_candidate.json"
```

Xem diem:

```powershell
Get-Content public_score_candidate.json
```

## 4. Danh gia

Uu tien cac chi so:

1. `n_correct` va `correct`
2. `prompt`
3. `quality`
4. `drift`
5. `latency` va `cost`

Khong chi nhin `headline`, vi diagnosis bonus co the day headline len 100 trong
khi correctness van chua cao.

Sau moi thay doi:

```powershell
python harness\selfcheck.py
python harness\synthetic_eval.py --out synthetic_score.json
```

## 5. Luu ket qua Public tot nhat

Chi thay file nop khi candidate moi tot hon:

```powershell
Copy-Item public_run_candidate.json run_output.json
Copy-Item public_score_candidate.json score.json
```

`run_output.json` va `score.json` phai la mot cap duoc tao tu cung mot lan chay.
Khong sua noi dung hai file vi scorer co chu ky.

## 6. Commit va Push

```powershell
git add solution run_output.json score.json
git commit -m "Submit best public result"
git push origin main
```

