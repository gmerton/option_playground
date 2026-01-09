import os, asyncio
from datetime import datetime, date
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.get_underlying_price import get_underlying_price
from lib.commons.list_expirations import list_expirations
from dateutil.relativedelta import relativedelta


# This module identifies opportunities for LEAP collar plays: long 100 shares, a protective ATM put, and a covered call.
# Been finding the LT skew column in oquants to be useful in pre-screening.

MAX_ANNUALIZED_BE_DRIFT = 8
MIN_ANNUALIZED_MAX_RETURN =  50.0
MIN_ANNUALIZED_MIN_RETURN = -12
MIN_REWARD_TO_RISK = 3


def find_call(spot, contracts, atm_put_contract):
    put_bid, put_ask = atm_put_contract["bid"], atm_put_contract["ask"]
    Kp = atm_put_contract["strike"]
    put_mid = (put_bid + put_ask) /2
   
    calls = [c for c in contracts if c.get("option_type").lower() == "call"]
    eligible = []
    
    
    for c in calls:
        bid, ask = c.get("bid"), c.get("ask")
        Kc = c["strike"]
        if bid is None or ask is None:
            continue
        call_mid = (bid + ask) / 2
        net_credit = call_mid - put_mid
        min_profit = -1*(spot - Kp - net_credit) * 100.0
     
     
        if min_profit >=0:
           eligible.append((call_mid,c))
    
    if not eligible:
        return None
    call =  min(
        eligible,
        key = lambda x:x[0]
    )[1]
    call_mid = (call["bid"] + call["ask"])/ 2

    return call



async def analyze(ticker, expiry, spot,  global_min_roi, verbose = False):
    dte = ((datetime.strptime(expiry, "%Y-%m-%d")).date() - date.today()).days
    
    #spot = await get_underlying_price(ticker)
    #spot = 15.28
    contracts = await list_contracts_for_expiry(ticker, expiry)
    if contracts is None:
        return
    if verbose:
        print(f"underlying spot={round(spot,2)}")
    tie_breaker = "higher"
    
    
    put_contracts = [c for c in contracts if c.get("option_type").lower() == "put"]
    call_contracts = [c for c in contracts if c.get("option_type").lower() == "call"]
    
    tie_breaker = "higher"
    prefer_high = (tie_breaker != "lower")
    atm_put_contract = min(
        put_contracts,
        key = lambda c: (
            abs(c["strike"]- spot),
            0 if (c["strike"] >= spot) == prefer_high else 1,
            c["strike"] if prefer_high else -c["strike"]
        )
    )
    put_bid, put_ask = atm_put_contract["bid"], atm_put_contract["ask"]
    if put_bid is None or put_ask is None:
        return
    put_mid = (put_bid + put_ask) /2
    breakeven_call_contract = find_call(spot, contracts, atm_put_contract)
    if breakeven_call_contract is None:
        return
    breakeven_call_contract_strike = breakeven_call_contract["strike"]
    atm_put_contract_strike = atm_put_contract["strike"]

    if verbose:
        # print(f"atm put strike ={atm_put_contract["strike"]}, price = {put_mid}")
        # print(f"call strike = {breakeven_call_contract_strike}")
        print(f"{ticker}, {expiry}")
    for call_contract in call_contracts:
        if call_contract["strike"] < breakeven_call_contract_strike:
            continue
        for put_contract in put_contracts:
            if put_contract["strike"] > atm_put_contract_strike or put_contract["strike"]>=call_contract["strike"]:
                continue
            if put_contract["bid"]==0 or call_contract["bid"]==0:
                continue
            
            if (call_contract["volume"]==0 and call_contract["open_interest"] < 50 and 
                (call_contract["last"] is not None and call_contract["ask"] > 2 * call_contract["last"]) and call_contract["ask"] > 5 * call_contract["bid"]
            ):
                continue
            if put_contract["bid"] is None or put_contract["ask"] is None or call_contract["bid"] is None or call_contract["ask"] is None:
                continue
            if put_contract["root_symbol"] != put_contract["underlying"] or call_contract["root_symbol"] != call_contract["underlying"]:
                continue
            global_min_roi = profitability(spot, call_contract, put_contract, dte, global_min_roi,  verbose)
    return global_min_roi



# MAX_ANNUALIZED_BE_DRIFT = 30
# MIN_ANNUALIZED_MAX_RETURN =  0
# MIN_ANNUALIZED_MIN_RETURN = 0
# MIN_REWARD_TO_RISK = 0

def profitability(spot, call_contract, put_contract, dte, global_min_roi, verbose = False):
    # strikes
    Kc = float(call_contract["strike"])
    Kp = float(put_contract["strike"])

    call_mid = (float(call_contract["bid"]) + float(call_contract["ask"])) /2.0
        
    put_mid = (float(put_contract["bid"]) + float(put_contract["ask"])) /2.0

    net_credit = call_mid - put_mid
    breakeven = round(spot + put_mid - call_mid,2)
    
    max_profit = (Kc - spot + net_credit) * 100.0
    min_profit = -1*(spot - Kp - net_credit) * 100.0

    initial_investment = (spot - net_credit) * 100.0
        
    min_return = round((min_profit / initial_investment) * 100,2)
    max_return = round((max_profit / initial_investment) * 100,2)

    annualized_min_return = round(100* (((1+min_return/100) ** (365/dte))-1),2)
    annualized_max_return = round(100* (((1+max_return/100) ** (365/dte))-1),2)
    

    reward_to_risk = -1 if min_profit == 0 else round(-1 * (max_profit) / (min_profit),1)
    term_BE_drift = (breakeven - spot) / spot
    annualized_BE_drift =100*((1+term_BE_drift) ** (365/dte) - 1)

    

    #if 1> 0:
    if annualized_BE_drift < MAX_ANNUALIZED_BE_DRIFT and annualized_max_return > MIN_ANNUALIZED_MAX_RETURN and annualized_min_return > MIN_ANNUALIZED_MIN_RETURN and (reward_to_risk >  MIN_REWARD_TO_RISK or reward_to_risk < 0):
        if global_min_roi is None or annualized_min_return > global_min_roi:
            global_min_roi = annualized_min_return
        if 1>0:
            print(f"{put_contract["expiration_date"]}, {round(initial_investment)}, Kp={Kp}, Kc={Kc}, max profit = {round(max_profit)}, max loss = {round(min_profit)}, Min ROI: {annualized_min_return}%, Max ROI: {annualized_max_return}%, r-to-r={reward_to_risk}, BE={breakeven}, BE_drift = {round(annualized_BE_drift,1)}%")
        if verbose:
            print(f"call price = {call_mid}, put price = {put_mid}")
    return global_min_roi
        

async def find_valid_expirations(ticker):
    unfiltered_exps = await list_expirations(ticker)
    today =date.today()
    six_months_later = today + relativedelta(months=5)
    filtered = [
        d for d in unfiltered_exps
        if datetime.strptime(d, "%Y-%m-%d").date() >= six_months_later
    ]
    return filtered

# Retrieve a list of exps 6 months or more in the future.
async def find_best_leap(ticker, spot = None, verbose=False):
    global_min_roi = None
    if spot == None:
        spot = await get_underlying_price(ticker)
        if spot is None:
            if verbose:
                print(f"Can't find spot for {ticker}")
            return
        if spot > 30:
            return
    # print(f"{ticker} spot={round(spot,2)}")
    
    filtered = await find_valid_expirations(ticker)
    for expiration_date in filtered:
        # print(ticker, expiration_date, "...")
        global_min_roi = await analyze(ticker, expiration_date, spot, global_min_roi, verbose)
    if global_min_roi is not None:
        print(f"{ticker}, {global_min_roi}")     

if __name__ == "__main__":
    #HPE: bad
    #APLD: good (1/15/2027)
    #HIMS: good
    #CHWY: mid
    #OXY bad
    #CMG mid
    #GTLB mid
    #BAC bad
    # SLV bad
    # Path mid
    # CPNG mid (14)
    # ONON bad
    # NVO bad
    # BROS bad
    # SIRI bad
    # KHC bad
    # BB mid (18)
    # HIVE bad
    # JBLUE good
    # AEO bad
    # BEKE bad
    # JOBY bad

    #GRAB 2027-01-15 ...Kp=5.5, Kc=10.0, max profit = 417, max loss = -33, Min ROI: -4.58%, Max ROI: 54.31%, r-to-r=12.6, BE=5.83, BE_drift = 2.5%
    #GRAB Kp=5.5, Kc=12.0, max profit = 600, max loss = -51, Min ROI: -6.82%, Max ROI: 74.47%, r-to-r=11.9, BE=6.0, BE_drift = 4.9%

    #GRAB, FUBO, AMC all have choices.
    #APLD has some expiring in 4/2026 that look good.
    # Kp=32.0, Kc=42.0, max profit = 854, max loss = -146, Min ROI: -8.58%, Max ROI: 58.2%, r-to-r=5.9, BE=33.45, BE_drift = -5.9%
    # NCLH bad
    # WRBY bad
    # SIRI bad
    # XPEV: 2027-01-15
    # UUUU: 2026-06-18, 2027-01-15
    # NLY 2026-04-17
    # RIOT multilple dates.  Best in 2026-05-15
    # MARA multiple. 
    # RUN: 2027-01-15
    # CAN: good
    # NB: good
    # DPRO: no
    # PATH: yes
    # ETH: yes
    # XRT: yes
    # ETHA: yes
    # IE: NO
    #AES: Yes
    # WBD: Yes
    #KHC: in buffet's portfolio. yes. But headed downhill.
    # QSI no
    # BTBT yes: has some nice ones due in May
    #tickers = [ "NB",  "ETH", "XRT", "ETHA", "AES", "WBD",  "HIMS", "CMG", "GRAB", "FUBO", "APLD", "XPEV", "UUUU",   "MARA"]
    
    big_list = ["A","AA","AAM","AAM.U","AAM.W","AAMI","AAP","AAT","AAUC","AB","ABBV","ABCB","ABEV","ABG","ABM","ABR","ABR$D","ABR$E","ABR$F","ABT","ABX","ABXL","ACA","ACCO","ACEL","ACH","ACHR","ACHR.W","ACI","ACLO","ACM","ACN","ACP","ACP$A","ACR","ACR$C","ACR$D","ACRE","ACV","ACVA","AD","ADC","ADC$A","ADCT","ADM","ADNT","ADT","ADX","AEE","AEFC","AEG","AEM","AEO","AER","AERO","AES","AESI","AEXA","AFB","AFG","AFGB","AFGC","AFGD","AFGE","AFL","AG","AGCO","AGD","AGI","AGL","AGM","AGM$D","AGM$E","AGM$F","AGM$G","AGM$H","AGM.A","AGO","AGRO","AGX","AHH","AHH$A","AHL","AHL$D","AHL$E","AHL$F","AHR","AHT","AHT$D","AHT$F","AHT$G","AHT$H","AHT$I","AI","AIG","AII","AIIA","AIIA.R","AIIA.U","AIN","AIO","AIR","AIT","AIV","AIZ","AIZN","AJG","AKA","AKAF","AKO.A","AKO.B","AKR","AL","ALB","ALB$A","ALC","ALEX","ALG","ALH","ALIT","ALK","ALL","ALL$B","ALL$H","ALL$I","ALL$J","ALLE","ALLY","ALSN","ALTG","ALTG$A","ALUB.U","ALUR","ALUR.W","ALV","ALX","AM","AMBP","AMBQ","AMC","AMCR","AME","AMG","AMH","AMH$G","AMH$H","AMN","AMP","AMPX","AMPX.W","AMPY","AMR","AMRC","AMRZ","AMT","AMTB","AMTD","AMTM","AMWL","AMX","AN","ANDG","ANET","ANF","ANG$D","ANGX","ANRO","ANVS","AOD","AOMD","AOMN","AOMR","AON","AORT","AOS","AP","APAM","APD","APG","APH","APLE","APO","APO$A","APOS","APTV","AQN","AQNB","AR","ARCO","ARDC","ARDT","ARE","ARES","ARES$B","ARI","ARL","ARLO","ARMK","AROC","ARR","ARR$C","ARW","ARX","AS","ASA","ASAN","ASB","ASB$E","ASB$F","ASBA","ASC","ASG","ASGI","ASGN","ASH","ASIC","ASIX","ASPN","ASR","ASX","ATEN","ATGE","ATH$A","ATH$B","ATH$D","ATH$E","ATHM","ATHS","ATI","ATKR","ATMU","ATO","ATR","ATS","AU","AUB","AUB$A","AUNA","AVA","AVAL","AVB","AVBC","AVD","AVK","AVNS","AVNT","AVTR","AVY","AWF","AWI","AWK","AWP","AWR","AX","AXIA","AXIA$","AXIA$C","AXL","AXP","AXR","AXS","AXS$E","AXTA","AYI","AZO","AZZ","B","BA","BA$A","BABA","BAC","BAC$B","BAC$E","BAC$K","BAC$L","BAC$M","BAC$N","BAC$O","BAC$P","BAC$Q","BAC$S","BAH","BAK","BALL","BALY","BAM","BANC","BANC$F","BAP","BARK","BAX","BB","BBAI","BBAI.W","BBAR","BBBY","BBBY.W","BBD","BBDC","BBDO","BBN","BBT","BBU","BBUC","BBVA","BBW","BBWI","BBY","BC","BC$C","BCAT","BCC","BCE","BCGD","BCH","BCO","BCS","BCSF","BCSM","BCSS","BCSS.U","BCSS.W","BCX","BDC","BDJ","BDN","BDX","BE","BEBE.U","BEKE","BEN","BEP","BEP$A","BEPC","BEPH","BEPI","BEPJ","BETA","BF.A","BF.B","BFAM","BFH","BFH$A","BFK","BFLY","BFLY.W","BFS","BFS$D","BFS$E","BFZ","BG","BGB","BGH","BGR","BGS","BGSF","BGSI","BGT","BGX","BGY","BH","BH.A","BHC","BHE","BHK","BHP","BHR","BHR$B","BHR$D","BHV","BHVN","BILL","BIO","BIO.B","BIP","BIP$A","BIP$B","BIPC","BIPH","BIPI","BIPJ","BIRK","BIT","BJ","BK","BK$K","BKD","BKE","BKH","BKKT","BKKT.W","BKN","BKSY","BKSY.W","BKT","BKU","BKV","BLCO","BLD","BLDR","BLE","BLK","BLND","BLSH","BLW","BLX","BMA","BME","BMEZ","BMI","BML$G","BML$H","BML$J","BML$L","BMN","BMO","BMY","BN","BNED","BNH","BNJ","BNL","BNS","BNT","BNY","BOC","BOE","BOH","BOH$A","BOH$B","BOND","BOOT","BORR","BOW","BOX","BP","BPRE","BR","BRBR","BRC","BRCC","BRCE","BRIE","BRK.A","BRK.B","BRO","BROS","BRSL","BRSP","BRT","BRW","BRX","BSAC","BSBR","BSL","BSM","BST","BSTZ","BSX","BTA","BTE","BTI","BTO","BTT","BTU","BTX","BTZ","BUD","BUI","BUR","BURL","BUXX","BV","BVN","BW","BW$A","BWA","BWG","BWLP","BWMX","BWNB","BWXT","BX","BXC","BXMT","BXMX","BXP","BXSL","BY","BYD","BYM","BZH","C","C$N","CAAP","CABO","CACI","CADE","CADE$A","CAE","CAF","CAG","CAH","CAL","CALX","CANG","CAPL","CARR","CARS","CAT","CATO","CAVA","CB","CBAN","CBL","CBNA","CBRE","CBT","CBU","CBZ","CC","CCI","CCID","CCIF","CCJ","CCK","CCL","CCM","CCO","CCS","CCU","CCZ","CDE","CDLR","CDP","CDR$B","CDR$C","CDRE","CE","CEE","CELG.R","CEPU","CF","CFG","CFG$E","CFG$H","CFG$I","CFND","CFR","CFR$B","CGAU","CGV","CHCT","CHD","CHE","CHGG","CHH","CHMI","CHMI$A","CHMI$B","CHPT","CHT","CHWY","CI","CIA","CIB","CICB","CIEN","CIF","CIG","CIG.C","CII","CIM","CIM$A","CIM$B","CIM$C","CIM$D","CIMN","CIMO","CIMP","CINT","CIO","CIO$A","CION","CIVI","CL","CLB","CLCO","CLDT","CLDT$A","CLF","CLH","CLPR","CLS","CLVT","CLW","CLX","CM","CMA","CMA$B","CMBT","CMC","CMCM","CMDB","CMG","CMI","CMP","CMPO","CMRE","CMRE$B","CMRE$C","CMRE$D","CMS","CMS$B","CMS$C","CMSA","CMSC","CMSD","CMTG","CMU","CNA","CNC","CNF","CNH","CNI","CNK","CNM","CNMD","CNNE","CNO","CNO$A","CNP","CNQ","CNR","CNS","CNX","CODI","CODI$A","CODI$B","CODI$C","COF","COF$I","COF$J","COF$K","COF$L","COF$N","COHR","COLD","COMP","CON","COOK","COP","COPL","COPL.U","COPL.W","COR","COSO","COTY","COUR","CP","CPA","CPAC","CPAI","CPAY","CPF","CPK","CPNG","CPRI","CPS","CPT","CQP","CR","CRBD","CRBG","CRC","CRCL","CRD.A","CRD.B","CRGY","CRH","CRI","CRK","CRL","CRM","CRS","CRT","CSAN","CSL","CSR","CSTM","CSV","CSW","CTA$A","CTA$B","CTBB","CTDD","CTEV","CTO","CTO$A","CTOS","CTRA","CTRE","CTRI","CTS","CTVA","CUBB","CUBE","CUBI","CUK","CULP","CURB","CURV","CUZ","CVE","CVE.W","CVEO","CVI","CVLG","CVNA","CVS","CVX","CW","CWAN","CWEN","CWEN.A","CWH","CWK","CWT","CX","CXE","CXH","CXM","CXT","CXW","CYD","CYH","D","DAC","DAL","DAN","DAO","DAR","DAVA","DAY","DB","DBD","DBI","DBL","DBRG","DBRG$H","DBRG$I","DBRG$J","DCI","DCO","DD","DDD","DDL","DDS","DDT","DE","DEA","DEC","DECK","DEI","DELL","DEO","DFH","DFIN","DFP","DG","DGX","DHF","DHI","DHR","DHT","DHX","DIAX","DIN","DINO","DIS","DIVY","DK","DKL","DKS","DLB","DLNG","DLNG$A","DLR","DLR$J","DLR$K","DLR$L","DLX","DLY","DMA","DMB","DMO","DNA","DNOW","DNP","DOC","DOCN","DOCS","DOLE","DOUG","DOV","DOW","DPG","DQ","DRD","DRI","DRLL","DSL","DSM","DSMC","DSTX","DSU","DSX","DSX$B","DSX.W","DT","DTB","DTE","DTF","DTG","DTK","DTM","DTW","DUK","DUK$A","DUKB","DV","DVA","DVN","DX","DX$C","DXC","DXYZ","DY","E","EAF","EAI","EARN","EAT","EB","EBF","EBS","EC","ECAT","ECC","ECC$D","ECCC","ECCF","ECCU","ECCV","ECCW","ECCX","ECG","ECL","ECO","ECVT","ED","EDD","EDF","EDN","EDU","EE","EEA","EEX","EFC","EFC$A","EFC$B","EFC$C","EFC$D","EFR","EFT","EFX","EFXT","EG","EGO","EGP","EGY","EHAB","EHC","EHI","EIC","EICA","EICC","EIG","EIIA","EIX","EL","ELAN","ELC","ELF","ELME","ELPC","ELS","ELV","EMA","EMBJ","EMD","EME","EMF","EMN","EMO","EMP","EMR","ENB","ENIC","ENJ","ENO","ENOV","ENR","ENS","ENVA","EOD","EOG","EOI","EOS","EOT","EP$C","EPAC","EPAM","EPC","EPD","EPR","EPR$C","EPR$E","EPR$G","EPRT","EQBK","EQH","EQH$A","EQH$C","EQNR","EQR","EQS","EQT","ERO","ES","ESAB","ESE","ESI","ESNT","ESRT","ESS","ESTC","ET","ET$I","ETB","ETD","ETG","ETI$","ETJ","ETN","ETO","ETR","ETSY","ETV","ETW","ETX","ETY","EVAC","EVAC.U","EVAC.W","EVC","EVEX","EVEX.W","EVF","EVG","EVH","EVMN","EVN","EVR","EVT","EVTC","EVTL","EVTR","EW","EXG","EXK","EXP","EXPD","EXR","F","F$B","F$C","F$D","FAF","FBIN","FBK","FBP","FBRT","FBRT$E","FC","FCF","FCN","FCPT","FCRS","FCRS.U","FCRS.W","FCRX","FCT","FCX","FDP","FDS","FDX","FE","FEDU","FEGE","FENG","FEOE","FERG","FET","FF","FFA","FFC","FFWM","FG","FGN","FGSN","FHI","FHN","FHN$C","FHN$E","FHN$F","FICO","FIG","FIGS","FIHL","FINS","FINV","FIS","FIX","FIXT","FLC","FLG","FLG$A","FLG$U","FLNG","FLO","FLOC","FLR","FLS","FLUT","FLXR","FMC","FMN","FMS","FMX","FMY","FN","FNB","FND","FNF","FNV","FOA","FOF","FOR","FOUR","FOUR$A","FPF","FPH","FPI","FR","FRA","FRGE","FRO","FRT","FRT$C","FSCO","FSK","FSM","FSS","FSSL","FT","FTHY","FTI","FTK","FTS","FTV","FTW","FTW.U","FTW.W","FTWO","FUBO","FUL","FUN","FVR","FVRR","FXED","G","GAB","GAB$G","GAB$H","GAB$K","GAM","GAM$B","GAP","GATX","GBAB","GBCI","GBTG","GBX","GCO","GCTS","GCTS.W","GCV","GD","GDDY","GDIV","GDL","GDO","GDOT","GDV","GDV$H","GDV$K","GE","GEF","GEF.B","GEL","GENI","GEO","GES","GETY","GEV","GF","GFF","GFI","GFL","GFR","GGB","GGG","GGT","GGT$E","GGT$G","GGZ","GHC","GHG","GHI","GHM","GHY","GIB","GIC","GIL","GIS","GJH","GJO","GJP","GJR","GJS","GJT","GKOS","GL","GL$D","GLOB","GLOP$A","GLOP$B","GLOP$C","GLP","GLP$B","GLW","GM","GME","GME.W","GMED","GMRE","GMRE$A","GMRE$B","GNE","GNK","GNL","GNL$A","GNL$B","GNL$D","GNL$E","GNRC","GNT","GNT$A","GNW","GOF","GOLD","GOLF","GOOS","GOTU","GPC","GPI","GPJA","GPK","GPMT","GPMT$A","GPN","GPOR","GPRK","GRBK","GRBK$A","GRC","GRDN","GRMN","GRND","GRNT","GROV","GRX","GS","GS$A","GS$C","GS$D","GSBD","GSK","GSL","GSL$B","GTES","GTLS","GTN","GTN.A","GTY","GUG","GUT","GUT$C","GVA","GWH","GWH.W","GWRE","GWW","GXO","GYLD","H","HAE","HAFN","HAL","HASI","HAYW","HBB","HBM","HCA","HCC","HCI","HCXY","HD","HDB","HE","HEI","HEI.A","HEQ","HESM","HF","HFEQ","HFGM","HFMF","HFND","HFRO","HFRO$A","HFRO$B","HG","HGER","HGLB","HGTY","HGV","HHH","HI","HIG","HIG$G","HII","HIMS","HIO","HIPO","HIW","HIX","HKD","HL","HL$B","HLF","HLI","HLIO","HLLY","HLLY.W","HLN","HLT","HLX","HMC","HMN","HMY","HNGE","HNI","HOG","HOMB","HOUS","HOV","HP","HPE","HPE$C","HPF","HPI","HPP","HPP$C","HPQ","HPS","HQH","HQL","HR","HRB","HRI","HRL","HRTG","HSBC","HSHP","HSY","HTB","HTD","HTFB","HTFC","HTGC","HTH","HTT","HUBB","HUBS","HUM","HUN","HUYA","HVT","HVT.A","HWM","HXL","HY","HYAC","HYAC.U","HYAC.W","HYBX","HYI","HYT","HYT.V","HYTR","HZO","IAE","IAG","IBM","IBN","IBP","IBTA","ICE","ICL","ICR$A","IDA","IDE","IDT","IEX","IFF","IFN","IFS","IGA","IGCB","IGD","IGI","IGR","IH","IHD","IHG","IHS","IIF","IIIN","IIM","IIPR","IIPR$A","IMAX","INFO","INFY","ING","INGM","INGR","INN","INN$E","INN$F","INR","INSP","INSW","INVH","INVX","IONQ","IONQ.W","IOT","IP","IPB","IPI","IQI","IQV","IR","IRM","IRS","IRS.W","IRT","ISD","IT","ITGR","ITT","ITUB","ITW","IVR","IVR$C","IVT","IVZ","IX","J","JACS","JACS.R","JACS.U","JBGS","JBI","JBK","JBL","JBND","JBS","JBTM","JCE","JCI","JEF","JELD","JENA","JENA.R","JENA.U","JFR","JGH","JHG","JHI","JHS","JHX","JILL","JKS","JLL","JLS","JMIA","JMM","JNJ","JOBY","JOBY.W","JOE","JOF","JPC","JPM","JPM$C","JPM$D","JPM$J","JPM$K","JPM$L","JPM$M","JQC","JRI","JRS","JXN","JXN$A","KAI","KB","KBDC","KBH","KBR","KD","KEN","KEP","KEX","KEY","KEY$I","KEY$J","KEY$K","KEY$L","KEYS","KF","KFRC","KFS","KFY","KGC","KGS","KIM","KIM$L","KIM$M","KIM$N","KIO","KKR","KKR$D","KKRS","KKRT","KLAR","KLC","KMI","KMPB","KMPR","KMT","KMX","KN","KNF","KNOP","KNSL","KNTK","KNX","KO","KODK","KOF","KOP","KORE","KOS","KR","KRC","KREF","KREF$A","KRG","KRMN","KRO","KRP","KRSP","KRSP.U","KRSP.W","KSS","KT","KTB","KTF","KTH","KTN","KVUE","KVYO","KW","KWR","KYN","L","LAC","LAD","LADR","LANV","LANV.W","LAR","LAW","LAZ","LB","LBRT","LC","LCII","LDI","LDOS","LDP","LEA","LEG","LEN","LEN.B","LEO","LEU","LEVI","LFT","LFT$A","LGI","LH","LHX","LII","LION","LITB","LLY","LMND","LMT","LNC","LNC$D","LND","LNG","LNN","LOAR","LOB","LOB$A","LOCL","LOMA","LOW","LPG","LPL","LPX","LRN","LSPD","LTC","LTH","LTM","LU","LUCK","LUMN","LUV","LUXE","LVS","LVWR","LVWR.W","LW","LXFR","LXP","LXP$C","LXU","LYB","LYG","LYV","LZB","LZM","LZM.W","M","MA","MAA","MAA$I","MAC","MAGN","MAIN","MAN","MANU","MAS","MATV","MATX","MAX","MBC","MBI","MC","MCB","MCD","MCI","MCK","MCN","MCO","MCR","MCS","MCY","MD","MDST","MDT","MDU","MDV","MDV$A","MEC","MED","MEG","MEGI","MEI","MER$K","MET","MET$A","MET$E","MET$F","MFA","MFA$B","MFA$C","MFAN","MFAO","MFC","MFG","MFM","MFSB","MFSG","MFSI","MFSM","MFSV","MG","MGA","MGF","MGM","MGR","MGRB","MGRD","MGRE","MGY","MH","MHD","MHF","MHK","MHLA","MHN","MHNC","MHO","MIAX","MICC","MIN","MIR","MITN","MITP","MITT","MITT$A","MITT$B","MITT$C","MIY","MKC","MKC.V","MKL","MLI","MLM","MLP","MLR","MMC","MMD","MMI","MMID","MMKT","MMM","MMS","MMT","MMU","MNR","MNSO","MNTN","MO","MOD","MODG","MOG.A","MOG.B","MOGU","MOH","MOS","MOV","MP","MPA","MPC","MPLX","MPV","MPW","MPX","MQT","MQY","MRK","MRP","MS","MS$A","MS$E","MS$F","MS$I","MS$K","MS$L","MS$O","MS$P","MS$Q","MSA","MSB","MSC","MSCI","MSD","MSDL","MSGE","MSGS","MSI","MSIF","MSM","MT","MTB","MTB$H","MTB$J","MTB$K","MTD","MTDR","MTG","MTH","MTN","MTR","MTRN","MTUS","MTW","MTX","MTZ","MUA","MUC","MUE","MUFG","MUJ","MUR","MUSA","MUSE","MUX","MVF","MVO","MVT","MWA","MX","MXE","MXF","MYD","MYE","MYI","MYN","NABL","NAC","NAD","NAN","NAT","NATL","NAZ","NBB","NBHC","NBR","NBXG","NC","NCA","NCDL","NCLH","NCV","NCV$A","NCZ","NCZ$A","NDMO","NE","NE.A","NE.W","NEA","NEE","NEE$N","NEE$S","NEE$T","NEE$U","NEM","NET","NEU","NEXA","NFG","NFJ","NGG","NGL","NGL$B","NGL$C","NGS","NGVC","NGVT","NHI","NI","NIC","NIE","NIM","NINE","NIO","NIQ","NJR","NKE","NKX","NL","NLOP","NLY","NLY$F","NLY$G","NLY$I","NLY$J","NMAI","NMAX","NMCO","NMG","NMI","NMM","NMR","NMS","NMT","NMZ","NNI","NNN","NNY","NOA","NOAH","NOC","NOG","NOK","NOM","NOMD","NOTE","NOTE.W","NOV","NOW","NP","NPB","NPCT","NPFD","NPK","NPKI","NPO","NPV","NPWR","NPWR.W","NQP","NRDY","NREF","NREF$A","NRG","NRGV","NRK","NRP","NRT","NRUC","NSA","NSA$A","NSA$B","NSC","NSP","NTB","NTR","NTST","NTZ","NU","NUE","NUS","NUV","NUVB","NUVB.W","NUW","NVG","NVGS","NVO","NVR","NVRI","NVS","NVST","NVT","NWAX.U","NWG","NWN","NX","NXC","NXDR","NXDT","NXDT$A","NXE","NXG","NXJ","NXN","NXP","NXRT","NYC","NYT","NZF","O","OAK$A","OAK$B","OBDC","OBK","OC","ODC","ODV","OEC","OFG","OGE","OGN","OGS","OHI","OI","OIA","OII","OIS","OKE","OKLO","OLN","OLP","OMC","OMF","ONIT","ONL","ONON","ONTF","ONTO","OOMA","OPAD","OPFI","OPFI.W","OPLN","OPP","OPP$A","OPP$B","OPTU","OPY","OR","ORA","ORC","ORCL","ORI","ORN","OSCR","OSG","OSK","OTF","OTIS","OUT","OVV","OWL","OWLT","OXM","OXY","OXY.W","PAAS","PAC","PACK","PACS","PAG","PAGS","PAI","PAII","PAII.U","PAII.W","PAM","PAR","PARR","PATH","PAXS","PAY","PAYC","PB","PBA","PBF","PBH","PBI","PBI$B","PBR","PBR.A","PBT","PCF","PCG","PCG$X","PCM","PCN","PCOR","PCQ","PD","PDCC","PDI","PDM","PDO","PDPA","PDS","PDT","PDX","PEB","PEB$E","PEB$F","PEB$G","PEB$H","PEG","PEN","PEO","PERF","PERF.W","PEW","PEW.W","PFD","PFE","PFGC","PFH","PFL","PFLT","PFN","PFO","PFS","PFSI","PG","PGP","PGR","PGZ","PH","PHG","PHI","PHIN","PHK","PHM","PHR","PII","PIM","PINE","PINE$A","PINS","PIPR","PJT","PK","PKE","PKG","PKST","PKX","PL","PL.W","PLD","PLNT","PLOW","PLYM","PM","PML","PMM","PMO","PMT","PMT$A","PMT$B","PMT$C","PMTU","PMTV","PMTW","PNC","PNFP","PNFP$A","PNFP$B","PNFP$C","PNI","PNNT","PNR","PNW","POR","POST","PPG","PPL","PPT","PR","PRA","PRCS","PRG","PRGO","PRH","PRI","PRIF$D","PRIF$J","PRIF$K","PRIF$L","PRIM","PRKS","PRLB","PRM","PRMB","PRS","PRSU","PRT","PRU","PRVS","PSA","PSA$F","PSA$G","PSA$H","PSA$I","PSA$J","PSA$K","PSA$L","PSA$M","PSA$N","PSA$O","PSA$P","PSA$Q","PSA$R","PSA$S","PSBD","PSEC$A","PSF","PSFE","PSN","PSO","PSQH","PSQH.W","PSTG","PSTL","PSX","PTA","PTY","PUK","PUMP","PVH","PVL","PWR","PX","PXED","PYT","Q","QBTS","QGEN","QSR","QTWO","QUAD","QVCC","QVCD","QXO","QXO$B","R","RA","RAC","RAC.U","RAC.W","RACE","RAL","RAMP","RBA","RBC","RBLX","RBOT","RBRK","RC","RC$C","RC$E","RCB","RCC","RCD","RCI","RCL","RCS","RCUS","RDDT","RDN","RDW","RDY","RELX","RERE","RES","REVG","REX","REXR","REXR$B","REXR$C","REZI","RF","RF$C","RF$E","RF$F","RFI","RFL","RFM","RFMZ","RGA","RGR","RGT","RH","RHI","RHLD","RHP","RIG","RIO","RITM","RITM$A","RITM$B","RITM$C","RITM$D","RITM$E","RIV","RIV$A","RJF","RKT","RL","RLI","RLJ","RLJ$A","RLTY","RLX","RM","RMAX","RMD","RMI","RMM","RMMZ","RMT","RNG","RNGR","RNP","RNR","RNR$F","RNR$G","RNST","ROG","ROK","ROL","RONB","RPM","RPT","RPT$C","RQI","RRC","RRX","RS","RSF","RSG","RSI","RSKD","RTO","RTX","RVLV","RVT","RVTY","RWT","RWT$A","RWTN","RWTO","RWTP","RWTQ","RXO","RY","RYAM","RYAN","RYI","RYN","RZB","RZC","S","SA","SABA","SAC.U","SAFE","SAH","SAJ","SAM","SAN","SAP","SAR","SARO","SAT","SAY","SAZ","SB","SB$C","SB$D","SBDS","SBH","SBI","SBR","SBS","SBSI","SBSW","SBXD","SBXD.U","SBXD.W","SBXE.U","SCCO","SCD","SCE$G","SCE$K","SCE$L","SCE$M","SCE$N","SCHW","SCHW$D","SCHW$J","SCI","SCL","SCM","SD","SDHC","SDHY","SDRL","SE","SEAL$A","SEAL$B","SEE","SEG","SEI","SEM","SEMR","SES","SES.W","SF","SF$B","SF$C","SF$D","SFB","SFBS","SFL","SG","SGHC","SGI","SGU","SHAK","SHCO","SHEL","SHG","SHO","SHO$H","SHO$I","SHOC","SHW","SI","SID","SIG","SII","SILA","SITC","SITE","SJM","SJT","SKE","SKIL","SKLZ","SKM","SKT","SKY","SKYH","SKYH.W","SLAI","SLB","SLF","SLG","SLG$I","SLGN","SLNZ","SLQT","SLVM","SM","SMA","SMBK","SMC","SMFG","SMG","SMHI","SMP","SMR","SMRT","SMWB","SN","SNA","SNAP","SNDA","SNDR","SNN","SNOW","SNX","SO","SOBO","SOC","SOJC","SOJD","SOJE","SOJF","SOLV","SOMN","SON","SONY","SOR","SOS","SOUL","SOUL.R","SOUL.U","SPB","SPCE","SPE","SPE$C","SPG","SPG$J","SPGI","SPH","SPHR","SPIR","SPMA","SPMC","SPME","SPNT","SPNT$B","SPOT","SPRU","SPXC","SPXX","SQM","SQNS","SR","SR$A","SRE","SREA","SRFM","SRG","SRG$A","SRI","SRL","SRV","SSB","SSD","SSL","SST","SSTK","ST","STAG","STC","STE","STEL","STEM","STEW","STG","STK","STLA","STM","STN","STNG","STRV","STT","STT$G","STUB","STVN","STWD","STXD","STXE","STXG","STXI","STXK","STXM","STXT","STXV","STZ","SU","SUI","SUN","SUNC","SUPV","SUZ","SVV","SW","SWK","SWX","SWZ","SXC","SXI","SXT","SYF","SYF$A","SYF$B","SYK","SYY","T","T$A","T$C","TAC","TAK","TAL","TALO","TAP","TAP.A","TBB","TBBB","TBI","TBLU","TBN","TCAI","TCBX","TCI","TCPA","TD","TDAY","TDC","TDF","TDG","TDOC","TDS","TDS$U","TDS$V","TDW","TDY","TE","TE.W","TECK","TEF","TEI","TEL","TEN","TEN$E","TEN$F","TEO","TEVA","TEX","TFC","TFC$I","TFC$O","TFC$R","TFII","TFIN","TFIN$","TFPM","TFSA","TFX","TG","TGE","TGLS","TGNA","TGS","TGT","THC","THG","THIR","THLV","THO","THQ","THR","THS","THW","TIC","TIMB","TISI","TJX","TK","TKC","TKO","TKR","TLK","TLYS","TM","TME","TMHC","TMO","TNC","TNET","TNGY","TNK","TNL","TOL","TOST","TPB","TPC","TPH","TPL","TPR","TPTA","TPVG","TPYP","TPZ","TR","TRAK","TRC","TREX","TRGP","TRN","TRNO","TROX","TRP","TRTN$A","TRTN$B","TRTN$C","TRTN$D","TRTN$E","TRTN$F","TRTX","TRTX$C","TRU","TRV","TS","TSE","TSI","TSLX","TSM","TSN","TSQ","TT","TTAM","TTC","TTE","TTI","TU","TUYA","TV","TVC","TVE","TWI","TWLO","TWN","TWO","TWO$A","TWO$B","TWO$C","TWOD","TX","TXNM","TXO","TXT","TY","TY$","TYG","TYL","U","UA","UAA","UAN","UBER","UBS","UCB","UDR","UE","UFI","UGI","UGP","UHAL","UHAL.B","UHS","UHT","UI","UIS","UL","ULS","UMC","UMH","UMH$D","UNF","UNFI","UNH","UNM","UNMA","UNP","UP","UPS","URI","USA","USAC","USB","USB$A","USB$H","USB$P","USB$Q","USB$R","USB$S","USFD","USNA","USPH","UTF","UTI","UTL","UTZ","UVE","UVV","UWMC","UZD","UZE","UZF","V","VAC","VACI","VACI.U","VACI.W","VAL","VAL.W","VALE","VATE","VBF","VCV","VEEV","VEL","VET","VFC","VG","VGI","VGM","VHI","VIA","VICI","VIK","VIPS","VIRT","VIST","VIV","VKQ","VLN","VLN.W","VLO","VLRS","VLT","VLTO","VMC","VMI","VMO","VNO","VNO$L","VNO$M","VNO$N","VNO$O","VNT","VOC","VOYA","VOYA$B","VOYG","VPG","VPV","VRE","VRT","VRTS","VSCO","VSH","VST","VSTS","VTEX","VTMX","VTN","VTOL","VTR","VTS","VVR","VVV","VVX","VYX","VZ","W","WAB","WAL","WAL$A","WAT","WBI","WBIY","WBS","WBS$F","WBS$G","WBX","WCC","WCN","WD","WDH","WDI","WDS","WEA","WEAV","WEC","WELL","WES","WEX","WF","WFC","WFC$A","WFC$C","WFC$D","WFC$L","WFC$Y","WFC$Z","WFG","WGO","WH","WHD","WHG","WHR","WIA","WINN","WIT","WIW","WK","WKC","WLK","WLKP","WLTG","WLY","WLYB","WM","WMB","WMK","WMS","WNC","WOLF","WOR","WPC","WPM","WPP","WRB","WRB$E","WRB$F","WRB$G","WRB$H","WRBY","WS","WSM","WSO","WSO.B","WSR","WST","WT","WTI","WTM","WTRG","WTS","WTTR","WU","WWW","WY","XFLT","XHR","XIFR","XOM","XPER","XPEV","XPO","XPOF","XPRO","XXI","XYF","XYL","XYZ","XZO","YALA","YCY","YCY.U","YCY.W","YELP","YETI","YEXT","YMM","YOU","YPF","YRD","YSG","YUM","YUMC","ZBH","ZEPP","ZETA","ZGN","ZH","ZIM","ZIP","ZKH","ZTO","ZTR","ZTS","ZVIA","ZWS"]

    ravish_list = ["AVGO",
"NVDA",
"GS",
"COST",
"META",
"BIDU",
"JPM",
"CRWD",
"PLTR",
"LULU",
"MSFT",
"TSLA",
"APP",
"WMT",
"TSM",
"ADBE",
"CAT",
"SNOW",
"COIN",
"NFLX",
"CRWV",
"PANW",
"ARM",
"ASML",
"XYZ",
"MU",
"SOFI",
"DELL",
"MS",
"JNJ",
"BAC",
"UBER",
"CHWY",
"CVNA",
"SGOV",
"GE",
"TGT",
"C",
"WFC",
"AMD",
"HPE",
"CMG",
"APLD",
"OXY",
"HD",
"QQQ",
"PEP",
"HIM",
"CRCL",
"FIG",
"SMCI",
"GTLB",
"DG",
"CRM"]
    
    small_list = ["ACH","ACHR","ACM","ACVA","AD","ADT","AI","AMC","AMPX","ANRO","APTV","ARLO","ASPN","AZO","BABA","BBAI","BE","BHVN","BKKT","BKV","BMY","BOX","BUD","BUR","BZH","CC","CCI","CF","CHGG","CMP","COMP","CON","CRCL","CTEV","CX","DE","DHR","DIS","DQ","EBS","ELF","FIG","FMC","FUBO","GIS","GME","HD","HHH","HIMS","HLT","HPQ","KEP","KO","KOS","KR","LAC","LDI","LEN","LMT","LNG","LUMN","MA","MANU","MBI","MCD","MO","MP","NEE","NIO","NOW","NPWR","NRGV","NUS","OKLO","OPFI","ORCL","OSG","PCG","PEG","PG","POST","QBTS","RACE","RDW","SAP","SES","SG","SHEL","SJM","SMR","SOC","SONY","SPGI","SRE","TIC","UNP","V","VG","VIPS","VNO","VZ","XXI"]

    smaller_list = ["HIMS", "AI", "ADT", "BOX", "ACHR", "BBAI", "BE", "ACVA", "CHGG", "QBTS"]

    tickers = ravish_list
    
    #for ticker in tickers:
    #for ticker in ["AG", "USAR", "QS", "SOUN", "HL", "LUNR", "CDE", "PL", "PAAS", "UUUU", "JD", "CRML","PATH", "LUNR", "SERV", "CDE", "QUBT", "INTC", "GLXY", "CLSK", "QBTS", "RGTI", "NVO"]:
    for ticker in smaller_list:
    #for ticker in ["ANVS"]:
    # for ticker in ["RKLB", "NLY", "HIMS", "AG", "VKTX","SOUN", "USAR", "PATH", "GME", "AG", "IONQ","QS",
    #                 "CCCX", "UUUU", "CDE", "LI"]:
    #for ticker in tickers:
    #for ticker in ["KVUE", "AIP", "SOUN", "AVTR", "FC", "NOMD", "MAX", "DOMO", "LX", "WPP", "CAG"]:
         # spot = 15.28
         spot = None
         asyncio.run(find_best_leap(ticker, spot, verbose=False))
         #asyncio.run(test("CMPO", '2026-03-20', True))
    
    
    
    #Run this for more details on a single idea
    #asyncio.run(test("JBLU", '2028-01-21', True))
    # asyncio.run(test("APLD", '2027-01-15', True))
 
 