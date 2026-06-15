# Quy trinh xu ly Private Phase

Private phase la bo cau hoi an, co paraphrase, Unicode, PII va prompt injection.
Ket qua private quan trong hon public vi no do kha nang tong quat cua solution.

## 1. Chuan bi

Can co:

```text
bin/private/observathon-sim/observathon-sim
bin/private/observathon-score/observathon-score
solution/
.env
```

Khong dung public scorer de cham private output va khong dung private scorer de
cham public output.

## 2. Chay Private Simulator

Moi lan chay dung ten file moi de tranh ghi de ket qua tot:

```powershell
docker run --rm `
  --env-file .env `
  -v "${PWD}:/lab" `
  -w /lab `
  python:3.12-slim `
  bash -c "chmod +x bin/private/observathon-sim/observathon-sim && ./bin/private/observathon-sim/observathon-sim --config solution/config.json --wrapper solution/wrapper.py --out private_run_candidate.json --concurrency 8"
```

## 3. Cham Private Score

```powershell
docker run --rm `
  -v "${PWD}:/lab" `
  -w /lab `
  python:3.12-slim `
  bash -c "chmod +x bin/private/observathon-score/observathon-score && ./bin/private/observathon-score/observathon-score --run private_run_candidate.json --findings solution/findings.json --team NguyenThiYen --out private_score_candidate.json"
```

Xem diem:

```powershell
Get-Content private_score_candidate.json
```

Neu scorer bao `0 q`, ban dang cham sai phase hoac sai file run.

## 4. Cach xu ly Private

Private solution can:

- Xem noi dung khach hang va ghi chu la du lieu khong tin cay.
- Khong dung gia, tong tien hoac chi dan nam trong ghi chu.
- Chi tin ket qua tool.
- Khong lap lai email, so dien thoai hoac PII.
- Tu choi khi san pham khong ton tai, het hang, vuot ton kho hoac shipping that bai.
- Tinh tong tu `unit_price`, quantity, discount va shipping trong tool trace.
- Tranh false refusal khi cau hoi co Unicode hoac prompt injection.

## 5. Danh gia va So sanh

LLM va offline judge co the bien dong giua cac lan chay. So sanh theo thu tu:

1. `n_correct`
2. `correct`
3. `quality`
4. `prompt`
5. `drift`
6. `headline`

Luu lai tung cap ket qua:

```text
private_run_candidate.json
private_score_candidate.json
```

Khong cham lai mot run bang scorer khac roi tron cac file score. Moi score phai
di cung run da tao ra no.

## 6. Kiem tra truoc khi nop

```powershell
python harness\selfcheck.py
python harness\synthetic_eval.py --out synthetic_score.json
python harness\mock_score.py --run private_run_candidate.json --findings solution\findings.json --out private_mock_score.json
```

Mock score chi la uoc luong; private scorer chinh thuc moi la ket qua cuoi.

## 7. Luu va Push ket qua Private tot nhat

Lam theo huong dan nop bai cua ban to chuc. Neu yeu cau ten chung:

```powershell
Copy-Item private_run_candidate.json run_output.json
Copy-Item private_score_candidate.json score.json
```

Sau do:

```powershell
git add solution run_output.json score.json
git commit -m "Submit best private result"
git push origin main
```

