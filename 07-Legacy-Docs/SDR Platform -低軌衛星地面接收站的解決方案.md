###### 作者：蔡秀吉
###### 撰寫日期：2023/09
# SDR Platform -低軌衛星地面接收站的解決方案
## 什麼是SDR Platform？
SDR Platform 指的是用來實現軟體無線電（Software Defined Radio，SDR）的硬體和軟體系統，SDR Platform 可以用來實現各種衛星的操作功能，（如：遙測接收、遙控指令傳輸和頻譜監測...）總而言之 SDR Platform 是一種靈活、高效益的衛星與地面接收站通訊的解決方案。

而軟體無線電(SDR) 呢，它是一種使用軟體來控制 RF 訊號處理的無線電。它比傳統無線電靈活度還要高，並且適應性更強，因為通常傳統無線電都是為了連接特定頻率，或是特定調製方案(modulation scheme)的來專門進行設計的。

以下簡介通用無線電系統的硬體設備及其職責：

![](https://hackmd.io/_uploads/SyeXurU1T.png)

> 通用無線電系統的 Physical Layer 處理和硬體設備示意圖
資料來源：A Software-Defined Baseband for Satellite Ground Operations

上圖最左邊橘色的部分，即是無線電系統前端的接收天線。無論你是用 Phased array、Control Plane Receiver 或是 User plane Receiver 一旦接收衛星通訊訊號之後，必然需要再進行後端處理，讓衛星訊號得以轉換成地面行動通訊訊號以供使用。

由於不同軌道的衛星會使用不同的通訊頻段（如：X, S, Ka, Ku band ...），所以傳統無線電系統的設計方式，會依據不同的頻段來設計專門的接收器、專門的 Up/Down Converter，甚至可以說專為特定頻段專門設計了整套無線電系統。
地面接收站接收到特定頻段之後，就會需要進行降頻處理，藉由將高頻的衛星通訊訊號降到中頻或是基頻，最後再經過基頻的系統處理，（上圖右邊藍色部分）將訊號轉換成 OSI 第三層（TCP/IP的網路層） 的 IP，後端就可以透過像是 Gateway 等設備，再介接電信基站、Wi-Fi Router、乙太網路，以供使用！

## 基於硬體的衛星地面接收站整體運行的架構圖
Hardware-based satellite ground operations architecture

![](https://hackmd.io/_uploads/rJQd_HU1a.png)

像上圖這類傳統基於硬體的衛星地面接收站，就會需要針對不同的衛星頻段（如：X band, S band ）來設計不同硬體和處理方式，雖然它看起來是一套系統，但是其實整合度不是很好，且整體硬體的複雜度很高。



## 基於軟體的衛星地面接收站整體運行的架構圖
SDR-based satellite ground operations architecture

![](https://hackmd.io/_uploads/HJm9dSLka.png)

像上圖這種基於軟體的地面接收站，基本上就可以有比較好的整合

那我們來看這類基於軟體的衛星地面接收站，它究竟是如何運行的。
最左邊衛星訊號的部分，通訊頻段可能是 X band, Ka band 等...不同頻段，假設現在是 Downlink 的情況，當天線接收到訊號之後，就會做一個比較 "general-purpose" Down Converter 的方式，將衛星訊號轉換到一個大一點的中頻(IF)。

![](https://hackmd.io/_uploads/S1fytSUkp.png)

轉換到中頻(IF)之後，即可透過一個能力很強的 SDR platform，general-purpose privated cloud 進行降頻轉換的處理，最後（上圖藍色部分）我們就可以全部都用 Baseband 的方式來進行後端的處理，像是轉成 IP 介接到 O-RAN 架構的基站、Ethernet、Wi-Fi Router 等...

## 基於SDR衛星地面接收站的瓶頸

![](https://hackmd.io/_uploads/BJrKtrIya.png)

左圖前面 RF 天線端的部分，當然如果可以的話，會希望盡量讓它更 genrnal purpose，就是說同一套的 SDR Platform，讓它盡量可以兼容接收多個不同的衛星頻段，像是 K band、Ku band 讓這類相近的頻段，可以用同一套的 SDR Platform 進行天線控制來接收並處理訊號，但是有些頻段可能沒辦法，頻段差太多還是得要用不同的 Up、Down Converter 來做基頻處理。

### 資料來源：
* Moses Browne Mwakyanjala. (2020). A Software-Defined Baseband for Satellite Ground Operations. https://www.diva-portal.org/smash/get/diva2:1502786/FULLTEXT05.pdf
* Mwakyanjala, Moses & Emami, Reza & Beek, Jaap. (2019). Functional Analysis of Software-Defined Radio Baseband for Satellite Ground Operations. Journal of Spacecraft and Rockets. 56. 1-18. 10.2514/1.A34333. 

### 其他
本文中文標題：基於SDR的低軌道衛星地面接收站解決方案
English Title: SDR-based satellite ground operations architecture

若是對於內容有任何想法或是對於 LEO 地面接收站介接 O-RAN 有興趣的話，歡迎與我聯繫，一起來討論交流~；現在時間凌晨 03:21 先打到這邊，我先來洗澡
撰文翻譯作者聯絡資訊（蔡秀吉）
* hctsai@linux.com
* thc1006@ieee.org
* https://www.facebook.com/thc1006