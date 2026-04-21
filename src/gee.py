import csv
import os
import sys
import argparse
from datetime import datetime, timedelta, timezone

import ee

# 石油備蓄基地タンク座標データ
TANK_DATA = [
    # 志布志国家備蓄基地 (shibushi)
    {"id": "shibushi_01", "lon": 131.02403931993155, "lat": 31.37539899202453},
    {"id": "shibushi_02", "lon": 131.02579884904532, "lat": 31.375545552003405},
    {"id": "shibushi_03", "lon": 131.02755837815909, "lat": 31.375673791797407},
    {"id": "shibushi_04", "lon": 131.02927499192862, "lat": 31.375783711481507},
    {"id": "shibushi_05", "lon": 131.0310345210424, "lat": 31.37594859076655},
    {"id": "shibushi_06", "lon": 131.02418952363638, "lat": 31.373896739059987},
    {"id": "shibushi_07", "lon": 131.02594905275015, "lat": 31.37404330138215},
    {"id": "shibushi_08", "lon": 131.0276871241918, "lat": 31.374153222973746},
    {"id": "shibushi_09", "lon": 131.02944665330557, "lat": 31.37431810512004},
    {"id": "shibushi_10", "lon": 131.03120618241934, "lat": 31.374446346589323},
    {"id": "shibushi_11", "lon": 131.03298716920523, "lat": 31.374592908054186},
    {"id": "shibushi_12", "lon": 131.02438264268545, "lat": 31.372412782672836},
    {"id": "shibushi_13", "lon": 131.0261207141271, "lat": 31.372559347309647},
    {"id": "shibushi_14", "lon": 131.02788024324087, "lat": 31.372687591179314},
    {"id": "shibushi_15", "lon": 131.02961831468252, "lat": 31.372815834873972},
    {"id": "shibushi_16", "lon": 131.0313778437963, "lat": 31.372925757901523},
    {"id": "shibushi_17", "lon": 131.03313737291006, "lat": 31.373090642201714},
    {"id": "shibushi_18", "lon": 131.02451138871817, "lat": 31.370873840184558},
    {"id": "shibushi_19", "lon": 131.02624946015982, "lat": 31.371075369801655},
    {"id": "shibushi_20", "lon": 131.0280089892736, "lat": 31.371166974030174},
    {"id": "shibushi_21", "lon": 131.02978997605948, "lat": 31.371331861416525},
    {"id": "shibushi_22", "lon": 131.03152804750113, "lat": 31.371405144606477},
    {"id": "shibushi_23", "lon": 131.03326611894278, "lat": 31.3715700315749},
    {"id": "shibushi_24", "lon": 131.023760370194, "lat": 31.369463120763676},
    {"id": "shibushi_25", "lon": 131.02551989930777, "lat": 31.369591368858845},
    {"id": "shibushi_26", "lon": 131.02730088609366, "lat": 31.369774580119746},
    {"id": "shibushi_27", "lon": 131.0290389575353, "lat": 31.36988450670486},
    {"id": "shibushi_28", "lon": 131.03079848664908, "lat": 31.370031075285006},
    {"id": "shibushi_29", "lon": 131.02395348924307, "lat": 31.367979094361466},
    {"id": "shibushi_30", "lon": 131.02571301835684, "lat": 31.368125665913265},
    {"id": "shibushi_31", "lon": 131.0274510897985, "lat": 31.36825391583357},
    {"id": "shibushi_32", "lon": 131.02921061891226, "lat": 31.368400486956755},
    {"id": "shibushi_33", "lon": 131.03097014802603, "lat": 31.368492093792675},
    {"id": "shibushi_34", "lon": 131.0241036929479, "lat": 31.366440079266983},
    {"id": "shibushi_35", "lon": 131.0258846797338, "lat": 31.36662329667114},
    {"id": "shibushi_36", "lon": 131.02760129350332, "lat": 31.36673322694221},
    {"id": "shibushi_37", "lon": 131.0293608226171, "lat": 31.366898122107735},
    {"id": "shibushi_38", "lon": 131.03114180940298, "lat": 31.367008052057344},
    {"id": "shibushi_39", "lon": 131.02427535432486, "lat": 31.36497432717624},
    {"id": "shibushi_40", "lon": 131.02603488343863, "lat": 31.365120903413885},
    {"id": "shibushi_41", "lon": 131.02775149720816, "lat": 31.36523083544215},
    {"id": "shibushi_42", "lon": 131.02953248399405, "lat": 31.365377411279812},
    {"id": "shibushi_43", "lon": 131.0312705554357, "lat": 31.36550566495024},
    # 苫小牧東部国家石油備蓄基地 (tomakomai)
    {"id": "tomakomai_00", "lon": 141.82418559966936, "lat": 42.646709328742595},
    {"id": "tomakomai_01", "lon": 141.82596658645525, "lat": 42.64603065242316},
    {"id": "tomakomai_02", "lon": 141.82324146209612, "lat": 42.64539931896693},
    {"id": "tomakomai_03", "lon": 141.82506536422625, "lat": 42.64470484476488},
    {"id": "tomakomai_04", "lon": 141.82684635101214, "lat": 42.64399457903931},
    {"id": "tomakomai_05", "lon": 141.82234023986712, "lat": 42.64407349785369},
    {"id": "tomakomai_06", "lon": 141.824121226653, "lat": 42.64336322492013},
    {"id": "tomakomai_07", "lon": 141.82594512878313, "lat": 42.642700296199344},
    {"id": "tomakomai_08", "lon": 141.82146047531023, "lat": 42.64274764848506},
    {"id": "tomakomai_09", "lon": 141.82317708907976, "lat": 42.642068928945626},
    {"id": "tomakomai_10", "lon": 141.82497953353777, "lat": 42.64134284868309},
    {"id": "tomakomai_11", "lon": 141.81947567548508, "lat": 42.65575355773517},
    {"id": "tomakomai_12", "lon": 141.82129421319718, "lat": 42.65505130864942},
    {"id": "tomakomai_13", "lon": 141.8185261734938, "lat": 42.65445162899561},
    {"id": "tomakomai_14", "lon": 141.82036616887802, "lat": 42.65374936520809},
    {"id": "tomakomai_15", "lon": 141.8176513689255, "lat": 42.653122212088135},
    {"id": "tomakomai_16", "lon": 141.8194162624573, "lat": 42.65243176951402},
    {"id": "tomakomai_17", "lon": 141.8167190069379, "lat": 42.65181743282421},
    {"id": "tomakomai_18", "lon": 141.81849999372378, "lat": 42.65113092125587},
    {"id": "tomakomai_19", "lon": 141.8211875671567, "lat": 42.651748996057194},
    {"id": "tomakomai_20", "lon": 141.82299537603274, "lat": 42.65106642922826},
    {"id": "tomakomai_21", "lon": 141.8202863449277, "lat": 42.65044698348372},
    {"id": "tomakomai_22", "lon": 141.82204587404146, "lat": 42.649768347943265},
    {"id": "tomakomai_23", "lon": 141.81932719895548, "lat": 42.649137850349554},
    {"id": "tomakomai_24", "lon": 141.82111891457743, "lat": 42.648459200525714},
    {"id": "tomakomai_25", "lon": 141.8184152478904, "lat": 42.6478258726383},
    {"id": "tomakomai_26", "lon": 141.82018550584024, "lat": 42.64714720850038},
    {"id": "tomakomai_27", "lon": 141.80584434414413, "lat": 42.64945707695635},
    {"id": "tomakomai_28", "lon": 141.80761460209396, "lat": 42.64879026753362},
    {"id": "tomakomai_29", "lon": 141.80492702866104, "lat": 42.64813923368598},
    {"id": "tomakomai_30", "lon": 141.80670801544693, "lat": 42.647456627243386},
    {"id": "tomakomai_31", "lon": 141.8093848600438, "lat": 42.64810372255286},
    {"id": "tomakomai_32", "lon": 141.81116562512364, "lat": 42.647409994031555},
    {"id": "tomakomai_33", "lon": 141.80847268727268, "lat": 42.64677472880722},
    {"id": "tomakomai_34", "lon": 141.81025367405857, "lat": 42.64609722973877},
    {"id": "tomakomai_35", "lon": 141.81295345527337, "lat": 42.64675114289606},
    {"id": "tomakomai_36", "lon": 141.81473444205926, "lat": 42.64606062959737},
    {"id": "tomakomai_37", "lon": 141.8120185632137, "lat": 42.645434296753265},
    {"id": "tomakomai_38", "lon": 141.8138156432537, "lat": 42.644747714733064},
    {"id": "tomakomai_39", "lon": 141.8164937722538, "lat": 42.64536926623439},
    {"id": "tomakomai_40", "lon": 141.81830158112984, "lat": 42.64468662939594},
    {"id": "tomakomai_41", "lon": 141.81558718560677, "lat": 42.64406317417814},
    {"id": "tomakomai_42", "lon": 141.81736392643302, "lat": 42.6433712037265},
    {"id": "tomakomai_43", "lon": 141.82006935524203, "lat": 42.644018605239516},
    {"id": "tomakomai_44", "lon": 141.80354552720644, "lat": 42.6442375653133},
    {"id": "tomakomai_45", "lon": 141.80524068330385, "lat": 42.64349572646194},
    {"id": "tomakomai_46", "lon": 141.8024941012726, "lat": 42.64297485559961},
    {"id": "tomakomai_47", "lon": 141.8042214438782, "lat": 42.64220143324396},
    {"id": "tomakomai_48", "lon": 141.8069787547455, "lat": 42.64272231058146},
    {"id": "tomakomai_49", "lon": 141.8087060973511, "lat": 42.64195677723178},
    {"id": "tomakomai_50", "lon": 141.80593805764772, "lat": 42.6414358934852},
    {"id": "tomakomai_51", "lon": 141.8076654002533, "lat": 42.64070191353155},
    {"id": "tomakomai_52", "lon": 141.81042271112062, "lat": 42.64120701894482},
    {"id": "tomakomai_53", "lon": 141.80941420053102, "lat": 42.63993635532248},
    {"id": "tomakomai_54", "lon": 141.80837350343324, "lat": 42.6386500221763},
    # 北海道石油協同備蓄基地 (hokkaido)
    {"id": "hokkaido_00", "lon": 141.8105962161876, "lat": 42.659163003974236},
    {"id": "hokkaido_01", "lon": 141.80967353628648, "lat": 42.65782958609832},
    {"id": "hokkaido_02", "lon": 141.8087401275493, "lat": 42.656535591118},
    {"id": "hokkaido_03", "lon": 141.8123518685402, "lat": 42.65848303804315},
    {"id": "hokkaido_04", "lon": 141.8141543129982, "lat": 42.65780449018832},
    {"id": "hokkaido_05", "lon": 141.8114506463112, "lat": 42.65714960558595},
    {"id": "hokkaido_06", "lon": 141.81322090426102, "lat": 42.65647893348349},
    {"id": "hokkaido_07", "lon": 141.8159352997841, "lat": 42.65711015448602},
    {"id": "hokkaido_08", "lon": 141.81770555773392, "lat": 42.65645526257124},
    {"id": "hokkaido_09", "lon": 141.81499116221084, "lat": 42.6557924733704},
    {"id": "hokkaido_10", "lon": 141.81679360666885, "lat": 42.655106005679635},
    {"id": "hokkaido_11", "lon": 141.81051299000677, "lat": 42.655850108344524},
    {"id": "hokkaido_12", "lon": 141.81231543446478, "lat": 42.655163641289974},
    {"id": "hokkaido_13", "lon": 141.80961176777777, "lat": 42.65454029107826},
    {"id": "hokkaido_14", "lon": 141.81139275456366, "lat": 42.65386170020035},
    {"id": "hokkaido_15", "lon": 141.81408573624196, "lat": 42.65449096707201},
    {"id": "hokkaido_16", "lon": 141.81586672302785, "lat": 42.65378870372867},
    {"id": "hokkaido_17", "lon": 141.81315232750478, "lat": 42.653165339735416},
    {"id": "hokkaido_18", "lon": 141.81493331429067, "lat": 42.65248673385488},
    {"id": "hokkaido_19", "lon": 141.8086365470965, "lat": 42.65325654299108},
    {"id": "hokkaido_20", "lon": 141.81046044922664, "lat": 42.652554265708574},
    {"id": "hokkaido_21", "lon": 141.8077675113757, "lat": 42.651922998462254},
    {"id": "hokkaido_22", "lon": 141.80955922699764, "lat": 42.65125226999259},
    {"id": "hokkaido_23", "lon": 141.81223070717647, "lat": 42.65186776227336},
    {"id": "hokkaido_24", "lon": 141.81401169396236, "lat": 42.65117336028532},
    {"id": "hokkaido_25", "lon": 141.8113187561114, "lat": 42.6505578611328},
    {"id": "hokkaido_26", "lon": 141.81308901406123, "lat": 42.649871335661665},
    {"id": "hokkaido_27", "lon": 141.8158034095843, "lat": 42.65050262373152},
    {"id": "hokkaido_28", "lon": 141.81756293869807, "lat": 42.649831879944564},
    {"id": "hokkaido_29", "lon": 141.81485927201106, "lat": 42.649200585067014},
    {"id": "hokkaido_30", "lon": 141.81666171646907, "lat": 42.648506153301405},
    # むつ小川原国家備蓄基地 (mutsu-ogawara)
    {"id": "mutsu_00", "lon": 141.27373326568215, "lat": 40.974647498109874},
    {"id": "mutsu_01", "lon": 141.27567518500894, "lat": 40.974404489589176},
    {"id": "mutsu_02", "lon": 141.27760637549966, "lat": 40.97419388148048},
    {"id": "mutsu_03", "lon": 141.27951610831826, "lat": 40.973902269143096},
    {"id": "mutsu_04", "lon": 141.2733792140922, "lat": 40.973213734898415},
    {"id": "mutsu_05", "lon": 141.27532113341897, "lat": 40.97297882157085},
    {"id": "mutsu_06", "lon": 141.2772523239097, "lat": 40.97270340488021},
    {"id": "mutsu_07", "lon": 141.27917278556436, "lat": 40.97248469080685},
    {"id": "mutsu_08", "lon": 141.2730573490104, "lat": 40.97176373928273},
    {"id": "mutsu_09", "lon": 141.2750207260093, "lat": 40.97148021686217},
    {"id": "mutsu_10", "lon": 141.27694118766397, "lat": 40.97125339804852},
    {"id": "mutsu_11", "lon": 141.27886164931863, "lat": 40.97101037702572},
    {"id": "mutsu_12", "lon": 141.28367889670938, "lat": 40.972363182675004},
    {"id": "mutsu_13", "lon": 141.28564227370828, "lat": 40.97239558486538},
    {"id": "mutsu_14", "lon": 141.28374326972573, "lat": 40.97089696690875},
    {"id": "mutsu_15", "lon": 141.2856637313804, "lat": 40.97092126909307},
    {"id": "mutsu_16", "lon": 141.28376472739785, "lat": 40.969414516737565},
    {"id": "mutsu_17", "lon": 141.28572810439675, "lat": 40.96943071855878},
    {"id": "mutsu_18", "lon": 141.28756273536294, "lat": 40.9724441881211},
    {"id": "mutsu_19", "lon": 141.2895368411979, "lat": 40.972460389198375},
    {"id": "mutsu_20", "lon": 141.2876271083793, "lat": 40.97094557126846},
    {"id": "mutsu_21", "lon": 141.28957975654214, "lat": 40.97097797415503},
    {"id": "mutsu_22", "lon": 141.28767002372354, "lat": 40.96946312218931},
    {"id": "mutsu_23", "lon": 141.28962267188638, "lat": 40.969519828504474},
    {"id": "mutsu_24", "lon": 141.29147876052468, "lat": 40.97247659027168},
    {"id": "mutsu_25", "lon": 141.2934635951957, "lat": 40.972525193467725},
    {"id": "mutsu_26", "lon": 141.29153240470498, "lat": 40.97101847774089},
    {"id": "mutsu_27", "lon": 141.29347432403176, "lat": 40.97104277988047},
    {"id": "mutsu_28", "lon": 141.29156459121316, "lat": 40.969544131196024},
    {"id": "mutsu_29", "lon": 141.29352796821206, "lat": 40.96956033298543},
    {"id": "mutsu_30", "lon": 141.29539478568643, "lat": 40.97256569610374},
    {"id": "mutsu_31", "lon": 141.2973367050132, "lat": 40.972614299234145},
    {"id": "mutsu_32", "lon": 141.29541624335855, "lat": 40.97109138413278},
    {"id": "mutsu_33", "lon": 141.2973903491935, "lat": 40.97113188764901},
    {"id": "mutsu_34", "lon": 141.29546988753884, "lat": 40.969617039217034},
    {"id": "mutsu_35", "lon": 141.29742253570168, "lat": 40.969633240988536},
    {"id": "mutsu_36", "lon": 141.29928522340492, "lat": 40.972631088064034},
    {"id": "mutsu_37", "lon": 141.30124860040382, "lat": 40.97265538960961},
    {"id": "mutsu_38", "lon": 141.29929595224098, "lat": 40.97117297894773},
    {"id": "mutsu_39", "lon": 141.301280786912, "lat": 40.97118918033719},
    {"id": "mutsu_40", "lon": 141.29938178292946, "lat": 40.969682434099845},
    {"id": "mutsu_41", "lon": 141.30134515992836, "lat": 40.96973103935427},
    {"id": "mutsu_42", "lon": 141.3031690620585, "lat": 40.9726958921657},
    {"id": "mutsu_43", "lon": 141.3051324390574, "lat": 40.97272019368742},
    {"id": "mutsu_44", "lon": 141.3032441639109, "lat": 40.97122158310413},
    {"id": "mutsu_45", "lon": 141.30519681207375, "lat": 40.97125398585517},
    {"id": "mutsu_46", "lon": 141.30326562158302, "lat": 40.96973103935427},
    {"id": "mutsu_47", "lon": 141.30523972741798, "lat": 40.96978774543916},
    {"id": "mutsu_48", "lon": 141.3070636295481, "lat": 40.97276879670401},
    {"id": "mutsu_49", "lon": 141.3070958160563, "lat": 40.97132689198681},
    {"id": "mutsu_50", "lon": 141.3071494602366, "lat": 40.96982824975566},
    # 福井国家備蓄基地 (fukui)
    {"id": "fukui_00", "lon": 136.10592584552893, "lat": 36.17796182530821},
    {"id": "fukui_01", "lon": 136.10753517093787, "lat": 36.177208385893024},
    {"id": "fukui_02", "lon": 136.10501389446387, "lat": 36.17667144763539},
    {"id": "fukui_03", "lon": 136.10663394870886, "lat": 36.175917995811524},
    {"id": "fukui_04", "lon": 136.10411267223486, "lat": 36.17538104871095},
    {"id": "fukui_05", "lon": 136.10568981113562, "lat": 36.174627584478515},
    {"id": "fukui_06", "lon": 136.1031618076184, "lat": 36.17408842863857},
    {"id": "fukui_07", "lon": 136.10477113302733, "lat": 36.17334361266908},
    {"id": "fukui_08", "lon": 136.10206746634032, "lat": 36.17253816417662},
    {"id": "fukui_09", "lon": 136.10364460524107, "lat": 36.171801994334835},
    {"id": "fukui_10", "lon": 136.10112100922117, "lat": 36.17126806254628},
    {"id": "fukui_11", "lon": 136.1027303346301, "lat": 36.17051455876574},
    {"id": "fukui_12", "lon": 136.10017464298386, "lat": 36.170006821490645},
    {"id": "fukui_13", "lon": 136.1018376125731, "lat": 36.169218660999775},
    {"id": "fukui_14", "lon": 136.09930560726303, "lat": 36.16864837242162},
    {"id": "fukui_15", "lon": 136.10091493267197, "lat": 36.16792082733175},
    {"id": "fukui_16", "lon": 136.09837219852585, "lat": 36.16736650273026},
    {"id": "fukui_17", "lon": 136.09999225277085, "lat": 36.16663028430779},
    {"id": "fukui_18", "lon": 136.09745292446723, "lat": 36.16609270386419},
    {"id": "fukui_19", "lon": 136.09907297871223, "lat": 36.16534781190191},
    {"id": "fukui_20", "lon": 136.09649963093653, "lat": 36.16479970465325},
    {"id": "fukui_21", "lon": 136.098023125657, "lat": 36.16394219798239},
    {"id": "fukui_22", "lon": 136.09546966267482, "lat": 36.16357589664345},
    {"id": "fukui_23", "lon": 136.0969609708871, "lat": 36.162744362179126},
    {"id": "fukui_24", "lon": 136.09439948961403, "lat": 36.16239141333309},
    {"id": "fukui_25", "lon": 136.0958907978263, "lat": 36.16151655632159},
    {"id": "fukui_26", "lon": 136.09335034813824, "lat": 36.1611453080847},
    {"id": "fukui_27", "lon": 136.09485238518658, "lat": 36.16027043716711},
    {"id": "fukui_28", "lon": 136.09742807449618, "lat": 36.160635212463376},
    {"id": "fukui_29", "lon": 136.09636591972628, "lat": 36.15941384736838},
]


def initialize_earth_engine(project_id=None):
    """Initialize the Earth Engine Python client."""
    try:
        if project_id:
            ee.Initialize(project=project_id)
        else:
            ee.Initialize()
    except Exception as e:
        print(f"Initialization failed: {e}")
        print("Please authenticate first: python -c 'import ee; ee.Authenticate()'")
        print("And provide a project ID: python gee.py --project YOUR_PROJECT_ID")
        raise


def get_region_from_id(tank_id):
    if '_' in tank_id:
        return tank_id.split('_', 1)[0]
    return 'unknown'


def group_tanks_by_region():
    regions = {}
    for tank in TANK_DATA:
        region = get_region_from_id(tank['id'])
        regions.setdefault(region, []).append(tank)
    return regions


def create_tank_geometries(tanks):
    # Earth Engine Geometryオブジェクトのリストを返す
    return [ee.Geometry.Point([tank["lon"], tank["lat"]]).buffer(40) for tank in tanks]


def load_sentinel1_collection(all_geom, start_date=None, end_date=None):
    if start_date is None:
        start_date = '2016-01-01T00:00:00Z'
    if end_date is None:
        end_date = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    collection_id = 'COPERNICUS/S1_GRD'
    polarizations = ['VV', 'VH', 'angle']

    ic = ee.ImageCollection(collection_id).filterBounds(all_geom).filterDate(start_date, end_date)

    ic = (
        ic.filter(ee.Filter.eq('instrumentMode', 'IW'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
        .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
    )

    return ic.select(polarizations)


def tank_time_series(tank_geom, s1_collection):
    def create_feature(img):
        stats = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=tank_geom,
            scale=20,
            maxPixels=1e6,
        )
        vv = stats.get('VV')
        vh = stats.get('VH')
        angle = stats.get('angle')
        return ee.Feature(
            None,
            {
                'date': img.date().format('YYYY-MM-dd'),
                'vv': vv,
                'vh': vh,
                'angle': angle,
                'system:time_start': img.get('system:time_start'),
            },
        )

    return s1_collection.map(create_feature).filter(ee.Filter.notNull(['vv', 'vh']))


def get_tank_series_info(tank_geom, tank_id, s1_collection):
    ts = (
        tank_time_series(tank_geom, s1_collection)
        .map(lambda f: f.set('t', f.get('system:time_start')))
        .filter(ee.Filter.notNull(['t']))
        .sort('t')
    )

    # データが存在しない場合、空の結果を返す
    size = ts.size()
    empty_result = ee.Dictionary({
        'tank_id': tank_id,
        'dates': [],
        'vvs': [],
        'vhs': [],
        'angles': [],
        'times': [],
    })

    def process_data():
        # 時系列データをサーバーサイドで注釈付け（変化点検出はローカルで実施）
        annotated = ts

        # 必要な統計量だけを取得
        dates = annotated.aggregate_array('date')
        vvs = annotated.aggregate_array('vv')
        vhs = annotated.aggregate_array('vh')
        angles = annotated.aggregate_array('angle')
        times = annotated.aggregate_array('t')

        return ee.Dictionary({
            'tank_id': tank_id,
            'dates': dates,
            'vvs': vvs,
            'vhs': vhs,
            'angles': angles,
            'times': times,
        })

    return ee.Algorithms.If(size.gt(0), process_data(), empty_result)


def get_last_datetime_from_csv(csv_path):
    """Get the latest datetime_utc from existing CSV file."""
    if not os.path.exists(csv_path):
        return None

    latest_dt = None
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            dt_str = row.get('datetime_utc')
            if not dt_str:
                continue
            try:
                # GEE の system:time_start はミリ秒なので int に変換
                dt = datetime.fromtimestamp(int(dt_str) / 1000, tz=timezone.utc)
                if latest_dt is None or dt > latest_dt:
                    latest_dt = dt
            except Exception:
                continue
    return latest_dt


def write_csv(file_path, rows, append=False):
    os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
    mode = 'a' if append else 'w'
    with open(file_path, mode=mode, newline='', encoding='utf-8') as csvfile:
        fieldnames = ['tank_id', 'date', 'datetime_utc', 'vv', 'vh', 'angle']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not append:
            writer.writeheader()
        writer.writerows(rows)


def parse_args():
    parser = argparse.ArgumentParser(description='Convert GEE JavaScript logic to Python Earth Engine API')
    parser.add_argument('--output-csv', default='tank_timeseries.csv', help='Base output CSV path or name')
    parser.add_argument('--output-dir', default='.', help='Output directory for region-based CSV files')
    parser.add_argument('--max-tanks', type=int, default=len(TANK_DATA), help='Number of tanks to process for the selected region or selected IDs')
    parser.add_argument('--tanks', nargs='+', help='Specific tank IDs to process (e.g., shibushi_01 shibushi_02)')
    parser.add_argument('--region', help='Specific region to process (e.g., shibushi, tomakomai, hokkaido)')
    parser.add_argument('--verbose', action='store_true', help='Print progress and summary')
    parser.add_argument('--project', help='Google Cloud project ID for Earth Engine')
    parser.add_argument('--update', action='store_true', help='Update mode: append new data to existing CSV')
    return parser.parse_args()


def get_output_csv_path(region, args):
    base_name = os.path.basename(args.output_csv)
    name_parts = base_name.rsplit('.', 1)
    if len(name_parts) == 2:
        name_base, ext = name_parts
        output_filename = f'{region}_{name_base}.{ext}'
    else:
        output_filename = f'{region}_{base_name}'

    if args.output_dir:
        return os.path.join(args.output_dir, output_filename)
    return output_filename


def select_tanks(region_tanks, args):
    if args.tanks:
        selected = [tank for tank in region_tanks if tank['id'] in args.tanks]
        if not selected:
            print(f"Error: No valid tank IDs found in {args.tanks} for this region")
        return selected
    return region_tanks[: args.max_tanks]


def process_region(region, region_tanks, args):
    output_csv = get_output_csv_path(region, args)

    # ★ 常に定義しておく（フルモードのデフォルト）
    start_date_str = None
    append_mode = False

    if args.update and os.path.exists(output_csv):
        last_dt = get_last_datetime_from_csv(output_csv)

        if last_dt:
            # 最終観測の 1 秒後を start_datetime にする
            start_dt = last_dt + timedelta(seconds=1)

            # GEE に渡す ISO8601 UTC 文字列
            start_date_str = start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

            # UTC の現在時刻
            now_utc = datetime.now(timezone.utc)

            # 未来ならこのリージョンはスキップ
            if start_dt > now_utc:
                print(f"No new data for {region}: start_datetime {start_dt} is in the future. Skipping.")
                return

            append_mode = True
            print(f"Update mode for {region}: appending data from {start_date_str}")

        else:
            # ★ CSV が空 or datetime_utc が無い → フルモードへ
            print(f"Warning: Could not determine last datetime for {output_csv}, falling back to full mode")
            start_date_str = None

    # ---- ここからは start_date_str が必ず存在する（None か文字列） ----

    selected_tanks = select_tanks(region_tanks, args)
    if not selected_tanks:
        return

    tanks = create_tank_geometries(selected_tanks)
    all_geom = ee.FeatureCollection([ee.Feature(t) for t in tanks]).geometry()

    # ★ start_date_str が None ならフルモード
    s1_collection = load_sentinel1_collection(all_geom, start_date=start_date_str)

    tank_stats = []
    for idx, tank in enumerate(selected_tanks):
        tank_id = tank['id']
        tank_geom = tanks[idx]
        if args.verbose:
            print(f'Processing tank {tank_id} in region {region}')
        stats = get_tank_series_info(tank_geom, tank_id, s1_collection)
        tank_stats.append(stats)

    all_stats = [ee.Dictionary(stat).getInfo() for stat in tank_stats]

    all_rows = []
    for stats in all_stats:
        dates = stats['dates']
        vvs = stats['vvs']
        vhs = stats['vhs']
        angles = stats['angles']

        for i in range(len(dates)):
            all_rows.append({
                'tank_id': stats['tank_id'],
                'date': dates[i],  # YYYY-MM-DD
                'datetime_utc': stats['times'][i],  # system:time_start (UTC ms)
                'vv': vvs[i],
                'vh': vhs[i],
                'angle': angles[i],
            })

    if not all_rows:
        print(f'No new time series data found for region {region}.')
        return

    write_csv(output_csv, all_rows, append=append_mode)
    print(f'{"Appended" if append_mode else "Wrote"} {len(all_rows)} rows to {output_csv}')

    if args.verbose:
        for row in all_rows[: min(10, len(all_rows))]:
            print(row)


def main():
    args = parse_args()
    initialize_earth_engine(args.project)

    regions = group_tanks_by_region()
    if args.region:
        if args.region not in regions:
            print(f'Error: Region {args.region} not found. Available regions: {sorted(regions.keys())}')
            return
        regions_to_process = {args.region: regions[args.region]}
    else:
        regions_to_process = regions

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir, exist_ok=True)

    for region, region_tanks in regions_to_process.items():
        print(f'Processing region: {region} ({len(region_tanks)} tanks)')
        process_region(region, region_tanks, args)


if __name__ == '__main__':
    main()
