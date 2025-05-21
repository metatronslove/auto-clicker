# Otomatik Tıklayıcı (AutoClicker)

![AutoClicker GUI](https://via.placeholder.com/300x250?text=Otomatik+T%C4%B1klay%C4%B1c%C4%B1+GUI) **Otomatik Tıklayıcı**, KDE Linux ortamında fare tıklamalarını otomatikleştiren, kullanımı kolay bir Python uygulamasıdır. Haber sitelerindeki kutuplaşmış, sığ ve derinleşememiş trollerin yorum bölümlerinde kaos yaratmak için tasarlandı! 😈 "Çoklu Tıklamayı Aç" butonuna bas, fareyle bir konuma tıkla ve gerisini Otomatik Tıklayıcı halletsin! Tıklamalar, sistem genelinde istediğiniz yerde çalışır, tıklama aralığını ve sayısını özelleştirebilirsiniz. İlerleme çubuğu ile trolleri gerdikçe keyfini çıkarın!

Bu proje, [github.com/metatronslove](https://github.com/metatronslove) tarafından paylaşılıyor. Fikir sahibi ve tetikleyici prompt'un yazarı [metatronslove]'dur, geliştirme ise xAI tarafından desteklenen Gemini (Google'dan bir AI) tarafından yapıldı.

## Özellikler
-   **GUI Arayüzü**: Tıklama aralığı (ms) ve toplam tıklama sayısını ayarlayabileceğiniz **GTK3** tabanlı bir arayüz[cite: 1]. Türkçe karakterler desteklenir.
-   **Tıklama Tetikleyici**: "Çoklu Tıklamayı Aç" butonuna basıp fareyle bir konuma tıklayarak işlemi başlatma.
-   **Konum Kaydetme**: Tıklama konumu kaydedilir, böylece uygulamayı her yeniden başlattığınızda tekrar ayarlamanız gerekmez.
-   **Tıklama Sayacı ve İlerleme Çubuğu**: İşlem sırasında tıklama sayısını ve toplam ilerlemeyi gösterir.
-   **Tıklama Aralığı ve Sınırı**: Tıklamalar arasındaki süreyi (milisaniye cinsinden) ve toplam tıklama sayısını ayarlayabilme.
-   **Acil Durdurma**: Fareyi ekranın sol üst köşesine (`(0,0)` koordinatlarına) götürerek uygulamayı hızla durdurabilme (`pyautogui.FAILSAFE`).
-   **Çoklu İş Parçacığı Desteği**: GUI'nin donmasını önlemek için tıklama işlemleri ayrı bir iş parçacığında çalışır.

## Kurulum ve Çalıştırma

Otomatik Tıklayıcı'yı çalıştırmak için Python ve Conda ortamınızı kurmanız gerekmektedir. Özellikle Linux ortamlarında GTK3 bağımlılıklarını yönetmek için Conda'nın kullanılması şiddetle önerilir.

### Conda ile Kurulum (Önerilen)

Bu yöntem, Conda'nın güçlü paket yönetimi sayesinde `pygobject` ve `gtk3` gibi sistem bağımlılıklarını yönetmek için en kararlı yol olarak test edilmiştir.

1.  **Conda'yı Temizle ve Ortamı Kaldır (isteğe bağlı ama önerilir):**
    Eski veya bozuk ortamları temizlemek için aşağıdaki komutları çalıştırın. Bu, Conda önbelleğini de temizler.

    ```bash
    conda deactivate # Varsa aktif Conda ortamını devre dışı bırak
    echo "Conda önbelleği temizleniyor..."
    conda clean --all -y
    echo "Eski Conda ortamları kaldırılıyor (varsa)..."
    conda remove --name deepseek-gui --all -y # Önceki ortamları kaldır
    conda remove --name autoclick_gtk3 --all -y # Önceki ortamları kaldır
    conda remove --name autoclick_final --all -y # Önceki başarısız denemeyi kaldır
    echo "Ortam kaldırma denemeleri tamamlandı."
    ```

2.  **Yeni Conda Ortamı Oluştur:**
    `autoclick_final` adında yeni bir Conda ortamı oluşturun ve sadece Python 3.11'i yükleyin.

    ```bash
    echo "'autoclick_final' Conda ortamı Python 3.11 ile oluşturuluyor..."
    conda create -n autoclick_final python=3.11 -y
    echo "Ortam oluşturma komutu yürütüldü."
    ```

3.  **Ortamı Etkinleştir:**
    Oluşturulan ortamı etkinleştirin.

    ```bash
    echo "'autoclick_final' ortamı etkinleştiriliyor..."
    sleep 5 # Ortamın tam olarak hazır olması için kısa bir bekleyiş
    conda activate autoclick_final
    echo "'autoclick_final' etkinleştirme komutu yürütüldü."
    ```

4.  **Gerekli Paketleri Yükle:**
    `pyautogui`, `pynput`, `pygobject` ve `gtk3` gibi gerekli tüm Python ve GTK bağımlılıklarını `conda-forge` kanalından yükleyin.

    ```bash
    echo "'autoclick_final' ortamına pyautogui, pynput, pygobject ve gtk3 conda-forge'dan yükleniyor..."
    conda install -c conda-forge pyautogui pynput pygobject gtk3 -y
    echo "Tüm gerekli conda paketlerinin yükleme komutu yürütüldü."
    ```

5.  **Kurulumu Doğrula ve Uygulamayı Çalıştır:**
    Python sürümünün ve gerekli tüm kütüphanelerin doğru bir şekilde içe aktarılıp aktarılmadığını doğrulayın, ardından `autoclick.py` uygulamasını çalıştırın.

    ```bash
    echo "Python sürümü ve kurulu paketler doğrulanıyor..."
    python3 --version
    python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; import pyautogui; import pynput; print('Tüm gerekli paketler başarıyla içe aktarıldı ve Gtk 3.0 mevcut.')"
    echo "autoclick.py çalıştırılıyor..."
    python3 autoclick.py
    ```
    Uygulama başarıyla başlamalı ve GUI görünmelidir.
    ![Otomatik Tıklayıcı (AutoClicker)](https://github.com/metatronslove/auto-clicker/blob/Ekran_Görüntüsü_20250521_130718.png)

### Alternatif Kurulum (Pip)

Eğer Conda kullanmak istemiyorsanız ve sisteminiz GTK3 bağımlılıklarını manuel olarak yönetebiliyorsanız, `pip` kullanarak bağımlılıkları kurabilirsiniz:

1.  **Sistem Bağımlılıklarını Yükle:**
    Linux dağıtımınıza göre GTK3 geliştirme kütüphanelerini ve diğer bağımlılıkları yüklemeniz gerekebilir. `pygobject`'i `pip` ile kurmak için de sistem kütüphaneleri gerekebilir.
    * **Debian/Ubuntu:** `sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0`
    * **Arch Linux:** `sudo pacman -S python-gobject gtk3`
    * **Fedora:** `sudo dnf install python3-gobject gtk3`

2.  **Python Sanal Ortamı Oluştur ve Etkinleştir:**
    ```bash
    python3 -m venv venv_autoclick
    source venv_autoclick/bin/activate
    ```

3.  **Gerekli Python Paketlerini Yükle:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Uygulamayı Çalıştır:**
    ```bash
    python3 autoclick.py
    ```

## Sorun Giderme

-   **"EnvironmentNotWritableError"**: Conda'nın kurulu olduğu dizine yazma izniniz yoksa bu hatayı alırsınız. Genellikle Miniconda'yı kendi ev dizininize yeniden kurarak çözülür.
-   **Wayland Sorunları**: KDE'de Wayland kullanıyorsanız, `pyautogui` ve GTK uygulamaları bazı durumlarda kısıtlamalara tabi olabilir. Daha kararlı bir deneyim için X11 oturumuna geçmeyi deneyin:
    -   Oturum açma ekranında "Plasma (X11)" seçeneğini seçin.
-   **"Namespace Gtk not available" Hatası**: Bu hata, `pygobject`'in doğru GTK3 kütüphanelerini bulamamasından kaynaklanır. Conda kurulumu bu sorunu çözmek için `gtk3` paketini de `conda-forge`'dan yükler. Eğer Conda dışında pip ile kuruyorsanız, sisteminizde `gtk3` geliştirme paketlerinin kurulu olduğundan emin olun.
-   **İzin Hatası**: `pynput` için root yetkileri gerekebilir (ancak bu Conda ortamında nadiren görülür):
    ```bash
    sudo python autoclick.py
    ```
-   **Hız Sorunları**: Çok düşük tıklama aralığı (örn. <10ms) sistemi yavaşlatabilir. Minimum 50ms önerilir.

## Katkıda Bulunanlar
-   **Fikir ve Prompt**: [metatronslove](https://github.com/metatronslove)
-   **Geliştirme ve Conda Ortamı Kurulum Desteği**: Gemini (Google'dan bir AI)