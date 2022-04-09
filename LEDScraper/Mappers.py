province_mapper = {
  'old_province': 'new_province',
  'กรุงเทพมหานคร': 'กรุงเทพมหานคร',
  'กรุงเทพ': 'กรุงเทพมหานคร'
}

district_mapper = {
  'new_province': {
    'old_district': [
      'potential_district_1',
      'potential_district_1'
    ]
  },
  'กรุงเทพมหานคร': {
    '(จรเข้บัว)ท่าแร้ง': ['38-ลาดพร้าว','ก1-ลาดพร้าว'],
    '(บางกะปิ)คันนายาว': ['06-บางกะปิ','ซ4-บางกะปิ','ซ5-บางกะปิ','บ1-บางกะปิ'],
    'คันนายาว(บึงกุ่ม)(บางกะปิ)': ['06-บางกะปิ','27-บึงกุ่ม','ซ4-บางกะปิ','ซ5-บางกะปิ','บ1-บางกะปิ'],
    'คันนายาว,บางกะปิ': ['06-บางกะปิ','ซ4-บางกะปิ','ซ5-บางกะปิ','บ1-บางกะปิ'],
    'คันนายาว,บางกะปิ': ['06-บางกะปิ','ซ4-บางกะปิ','ซ5-บางกะปิ','บ1-บางกะปิ'],
    'จตุจักร': ['30-จตุจักร'],
    'จอมทอง': ['35-จอมทอง'],
    'เจียระดับ': ['ล2-เจียระดับ'],
    'เจียรดับ': ['ล2-เจียระดับ'],
    'ดอนเมือง': ['36-ดอนเมือง'],
    'ดินแดง': ['26-ดินแดง'],
    'ดุสิต': ['02-ดุสิต','ซ6-ดุสิต'],
    'ตลิ่งชัน': ['19-ตลิ่งชัน','อ1-ตลิ่งชัน(บางใหญ่)'],
    '(บางกะปิ)บางเขน': ['05-บางเขน','06-บางกะปิ','ข4-บางเขน(เมือง)','ซ4-บางกะปิ','ซ5-บางกะปิ','ด3-บางเขน(เมือง)','ด4-บางเขน(ตลาดขวัญ)','บ1-บางกะปิ'],
    'ทวีวัฒนา': ['48-ทวีวัฒนา'],
    'ทุ่งครุ': ['49-ทุ่งครุ'],
    'ธนบุรี': ['15-ธนบุรี'],
    'บางกอกน้อย': ['20-บางกอกน้อย'],
    'บางกอกใหญ่': ['16-บางกอกใหญ่'],
    'บางกะปิ': ['06-บางกะปิ','ซ4-บางกะปิ','ซ5-บางกะปิ','บ1-บางกะปิ'], 
    'บางขุนเทียน': ['21-บางขุนเทียน','ต2-บางขุนเทียน(เมืองสมุ','ท2-บางขุนเทียน(เมือง)'], 
    'บางเขน': ['05-บางเขน','ข4-บางเขน(เมือง)','ด3-บางเขน(เมือง)','ด4-บางเขน(ตลาดขวัญ)'], 
    'บางเขน(สายไหม)': ['05-บางเขน','42-สายไหม','ข4-บางเขน(เมือง)','ด3-บางเขน(เมือง)','ด4-บางเขน(ตลาดขวัญ)'],
    'บางเขน(บางกะปิ)': ['05-บางเขน','06-บางกะปิ','ข4-บางเขน(เมือง)','ซ4-บางกะปิ','ซ5-บางกะปิ','ด3-บางเขน(เมือง)','ด4-บางเขน(ตลาดขวัญ)','บ1-บางกะปิ'], 
    'คลองเตย': ['33-คลองเตย'], 
    'บางเขน(ลาดพร้าว)': ['05-บางเขน','38-ลาดพร้าว','ก1-ลาดพร้าว','ข4-บางเขน(เมือง)','ด3-บางเขน(เมือง)','ด4-บางเขน(ตลาดขวัญ)'],
    'บางเขน(ลำลูกกา)': ['05-บางเขน','ข5-บางเขน(ลำลูกกา)','ข4-บางเขน(เมือง)','ด3-บางเขน(เมือง)','ด4-บางเขน(ตลาดขวัญ)'], 
    'บางคอแหลม': ['31-บางคอแหลม'], 
    'บางแค': ['40-บางแค'], 
    'บางซื่อ': ['29-บางซื่อ','ซ1-บางซื่อ','ซ2-บางซื่อ'], 
    'บางนา': ['47-บางนา'],
    'บางบอน': ['50-บางบอน'], 
    'บางพลัด': ['25-บางพลัด'], 
    'บางรัก': ['04-บางรัก','ซ7-บางรัก'], 
    'บางลำภูล่าง': ['18-คลองสาน','ธ1-คลองสาน(บางลำภูล่าง)'], 
    'คลองสาน': ['18-คลองสาน','ธ1-คลองสาน(บางลำภูล่าง)'],
    'บึงกุ่ม': ['27-บึงกุ่ม'], 
    'บึงกุ่ม(บางกะปิ)': ['06-บางกะปิ', '27-บึงกุ่ม','ซ4-บางกะปิ','ซ5-บางกะปิ','บ1-บางกะปิ'], 
    'บุคคโล': ['15-ธนบุรี'], 
    'ปทุมวัน': ['07-ปทุมวัน'],
    'ประแจจีน': ['37-ราชเทวี'], 
    'ประเวศ': ['32-ประเวศ'], 
    'ป้อมปราบ': ['08-ป้อมปราบศัตรูพ่าย'], 
    'ป้อมปราบศัตรูพ่าย': ['08-ป้อมปราบศัตรูพ่าย'],
    'พญาไท': ['14-พญาไท'], 
    'พระโขนง': ['09-พระโขนง','ซ3-พระโขนง'], 
    'คลองสามวา': ['46-คลองสามวา'], 
    'พระนคร': ['01-พระนคร','ส1-พระนคร(ในพระนคร)'], 
    'ภาษีเจริญ': ['22-ภาษีเจริญ'],
    'มีนบุรี': ['10-มีนบุรี','ม2-มีนบุรี(เมือง)'], 
    'มีนบุรี(เมือง)': ['10-มีนบุรี','ม2-มีนบุรี(เมือง)'], 
    'มีนบุรี(แสนแสบ)': ['10-มีนบุรี','ม2-มีนบุรี(เมือง)','ม3-แสนแสบ'],
    'มีนบุรี(บางชัน)': ['10-มีนบุรี','ม2-มีนบุรี(เมือง)'], 
    'มีนบุรี(เมือง)': ['10-มีนบุรี','ม2-มีนบุรี(เมือง)'], 
    'มีนบุรี(แสนแสบ)': ['10-มีนบุรี','ม2-มีนบุรี(เมือง)','ม3-แสนแสบ'],
    'ยานนาวา': ['12-ยานนาวา','ส6-ยานนาวา(เมือง)'], 
    'คลองสามวา (มีนบุรี)': ['10-มีนบุรี','46-คลองสามวา','ม2-มีนบุรี(เมือง)'], 
    'ราชเทวี': ['37-ราชเทวี'], 
    'ราษฎร์บูรณะ': ['24-ราษฎร์บูรณะ','ท3-ราษฎร์บูรณะ','ธ2-ราษฎร์บูรณะ(เมือง)'],
    'ลาดกระบัง': ['11-ลาดกระบัง'],
    'ลาดกระบัง(แสนแสบ)': ['11-ลาดกระบัง','ม3-แสนแสบ'],
    'ลาดกระบัง(คลองประเวศบุรีรมย์)': ['11-ลาดกระบัง'],
    'ลาดกระบัง(คลองประเวศบุรีรมย์ฝั่งเหนือ)': ['11-ลาดกระบัง'], 
    'ลาดกระบัง(เจียระดับ)': ['11-ลาดกระบัง','ล2-เจียระดับ'],
    'ลาดกระบัง(แสนแสน)': ['11-ลาดกระบัง'], 
    'ลาดกระบัง(แสนแสบ)': ['11-ลาดกระบัง','ม3-แสนแสบ'], 
    'ลาดพร้าว': ['38-ลาดพร้าว','ก1-ลาดพร้าว'],
    'คลองสามวา(มีนบุรี)':['10-มีนบุรี','46-คลองสามวา','ม2-มีนบุรี(เมือง)'], 
    'ลาดพร้าว(บางกะปิ)': ['06-บางกะปิ','38-ลาดพร้าว','ก1-ลาดพร้าว','ซ4-บางกะปิ','ซ5-บางกะปิ','บ1-บางกะปิ'], 
    'ลาดพร้าว(บางกะปิ)': ['06-บางกะปิ','38-ลาดพร้าว','ก1-ลาดพร้าว','ซ4-บางกะปิ','ซ5-บางกะปิ','บ1-บางกะปิ'],
    'วังทองหลาง': ['45-วังทองหลาง'], 
    'วัฒนา': ['39-วัฒนา'], 
    'สวนหลวง': ['34-สวนหลวง'], 
    'สะพานสูง': ['44-สะพานสูง'],
    'สะพานสูง(บึงกุ่ม)': ['27-บึงกุ่ม','44-สะพานสูง'], 
    'สัมพันธวงศ์': ['13-สัมพันธวงศ์'], 
    'สาทร': ['28-สาทร'], 
    'สามเพ็ง': ['ส9-สามเพ็ง'],
    'คันนายาว': ['43-คันนายาว'], 
    'สายไหม': ['42-สายไหม'], 
    'สายไหม(บางเขน)': ['05-บางเขน','42-สายไหม','ข4-บางเขน(เมือง)','ด3-บางเขน(เมือง)','ด4-บางเขน(ตลาดขวัญ)'], 
    'หนองแขม': ['23-หนองแขม'], 
    'หนองจอก': ['03-หนองจอก'],
    'หนองจอก(เจียรดับ)': ['03-หนองจอก','ล2-เจียระดับ'], 
    'หนองจอก(เจียระดับ)': ['03-หนองจอก','ล2-เจียระดับ'],
    'หนองจอก(เจียระัดับ)': ['03-หนองจอก','ล2-เจียระดับ'], 
    'หนองจอก(แสนแสบ)': ['03-หนองจอก','ม3-แสนแสบ'], 
    'หลักสี่': ['41-หลักสี่'],
    'ห้วยขวาง': ['17-ห้วยขวาง'], 
    'คันนายาว(บางกะปิ)': ['06-บางกะปิ','43-คันนายาว','ซ4-บางกะปิ','ซ5-บางกะปิ','บ1-บางกะปิ']
  }
}