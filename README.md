# Sky Hunt

Bu proje, kamerayı arka planda kullanan ve ekranda yalnızca gökyüzü, bulutlar ve ördeklerden oluşan bir oyun sahnesi gösteren bir el kontrolü oyunudur.

## Özellikler

- Kızılötesi gibi bulutlu gökyüzü ve kayan manzara
- Soldan/sağdan gelen ördekler
- El hareketiyle nişan alma
- Parmakların bir araya gelmesi (pinch) ile ateş etme
- Skor ve can sistemi
- Görüntüde gerçek kameranın görünmemesi

## Çalıştırma

```bash
pip install -r requirements.txt
python main.py
```

## Kontrol

- Nişan almak: index parmağı ile kameradaki el hareketini takip et
- Ateş etmek: baş parmak ile işaret parmağını birleştir (pinch)
- Çıkış: `q`

## Not

Bu sürüm, mevcut AR portal sistemini tamamen oyuna dönüştürür; doğrudan görüntüleme ekranı yerine oyun sahnesi gösterilir.
