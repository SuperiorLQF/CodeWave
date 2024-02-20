# parameter
# param_color
SKIP_LST                =   []
SCALE                   =   1
SIG_MANNER              =   ['bin','sig']
SIG_GREEN               =   "#229933"
WAVE_HEIGHT             =   100
WAVE_ORIGIN_STARTX      =   200
WAVE_ORIGIN_STARTY      =   200 
ORIGIN_POINT            =   (WAVE_ORIGIN_STARTX,WAVE_ORIGIN_STARTY)
END_TIME                =   0
SKIP_LEN                =   50
WAVE_LST                =   []

#[解析层MAIN]：读取文件存入列表
def get_lines():
    # 打开文件  
    with open('wavecode.cdw', 'r') as file:  
        # 读取所有行  
        lines = file.readlines()  
    #print(lines)
    return lines

#[解析层MAIN]：获取参数
def get_args(lines):
    global END_TIME,SCALE,SKIP_LST
    for line in lines:
        element_lst = line.split()
        #找出ENDTIME
        if(len(element_lst) >=2):
            if  (element_lst[0] == '@end'   ):
                END_TIME = eval(element_lst[1])
            #找出SCALE
            elif(element_lst[0] == '@scale' ):
                SCALE    = eval(element_lst[1])
            #找出SKIP
            elif(element_lst[0] == '@skip'  ):
                SKIP_LST.append([eval(element_lst[1]),eval(element_lst[-1])])

#[解析层MAIN]：获取波形初始点
def get_wave(lines):
    global  WAVE_LST
    #WAVE_LST 包含WAVE_DICT的列表，表示全体波形
    #WAVE_DICT 表示一个波形，属性有sig_name,sig_manner,sig_color,sig_linewidth,point_lst(相对时间转换),point_lst_insert(插入点转换),point_lst_read_coord(转换为绘图坐标)
    WAVE_DICT={}
    Flag_in_sig = False
    sig_index   = 0
    for line in lines:
        element_lst = line.split()
        if(Flag_in_sig == True):
            if(len(element_lst)!=2):#退出
                #插入点处理，目前的坐标还是时间坐标，value也还是1和0
                WAVE_DICT['point_lst_insert']=sigline_to_pointslst(WAVE_DICT['point_lst'])
                WAVE_LST.append(WAVE_DICT.copy()) 
                #后处理
                Flag_in_sig = False
                WAVE_DICT   = {}
                sig_index += 1
            else:#中间
                WAVE_DICT['point_lst'].append([eval(element_lst[0]),eval(element_lst[1])])
                
        if(len(element_lst) == 4):
            if(element_lst[1] in SIG_MANNER):#进入
                (sig_name,sig_manner,sig_color,sig_linewidth)=(element_lst[0][1:],element_lst[1],element_lst[2],element_lst[3])
                WAVE_DICT['sig_name']       = sig_name
                WAVE_DICT['sig_manner']     = sig_manner
                WAVE_DICT['sig_color']      = sig_color
                WAVE_DICT['sig_linewidth']  = eval(sig_linewidth)
                WAVE_DICT['sig_index']      = sig_index
                WAVE_DICT['point_lst']      = []
                Flag_in_sig = True

#[解析层MAIN step1]:在WAVE_DICT加上新的键,skip处理
def cal_skip_insert():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:
        point_lst_real_coord=[]
        point_lst_real_coord.append(WAVE_DICT['point_lst_insert'][0])#point
        for point_index in range(0,len(WAVE_DICT['point_lst_insert'])-1):
            for section in SKIP_LST:
                skip_start = section[0]
                skip_end   = section[1]
                if(skip_start>=WAVE_DICT['point_lst_insert'][point_index][0] and skip_end<=WAVE_DICT['point_lst_insert'][point_index+1][0]):
                    point_lst_real_coord.append([section[0],2])#section start
                    point_lst_real_coord.append([section[1],2.5])#section end

            point_lst_real_coord.append(WAVE_DICT['point_lst_insert'][point_index+1])#point
        
        WAVE_DICT['point_lst_insert_skip'] = point_lst_real_coord
        
#[解析层MAIN step2]:在point_lst_insert_skip基础上计算真实坐标，不考虑skip compress和scale
def cal_real_coord_x():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:
        point_lst_insert_skip_realx=[]
        for point in WAVE_DICT['point_lst_insert_skip']:
            point_lst_insert_skip_realx.append([point[0]+WAVE_ORIGIN_STARTX ,point[1]])
        WAVE_DICT['point_lst_insert_skip_realx'] = point_lst_insert_skip_realx
    pass

#[解析层MAIN step3]:在point_lst_insert_skip_realx基础上计算真实坐标，不考虑skip compress,考虑scale
def cal_real_coord_x_scale():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:
        point_lst_insert_skip_realx_scale=[]
        for point in WAVE_DICT['point_lst_insert_skip_realx']:
            point_lst_insert_skip_realx_scale.append([(point[0]-WAVE_ORIGIN_STARTX)*SCALE+WAVE_ORIGIN_STARTX ,point[1]])
        WAVE_DICT['point_lst_insert_skip_realx_scale'] = point_lst_insert_skip_realx_scale
    pass

#[解析层MAIN step4]:在point_lst_insert_skip_realx_scale基础上计算真实坐标，考虑skip compress,考虑scale
def cal_real_coord_x_scale_skipadjust():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:
        point_lst_insert_skip_realx_scale_skipadjust=WAVE_DICT['point_lst_insert_skip_realx_scale'][:]#复制列表
        for i in range(len(point_lst_insert_skip_realx_scale_skipadjust)):
            point = point_lst_insert_skip_realx_scale_skipadjust[i]
            if(point[1] == 2):
                section_start = point[0]
                section_end   = point_lst_insert_skip_realx_scale_skipadjust[i+1][0]
                section_diff  = section_end - section_start #原本skip区间的实际位置差距
                section_new   = SKIP_LEN #调整后的skip区间长度
                skip_change   = SKIP_LEN - section_diff#最终区间右端点及之后的点需要调整的值
                for j in range(i+1,len(point_lst_insert_skip_realx_scale_skipadjust)):
                    point_lst_insert_skip_realx_scale_skipadjust[j]=[point_lst_insert_skip_realx_scale_skipadjust[j][0]+skip_change,point_lst_insert_skip_realx_scale_skipadjust[j][1]] 
                
        WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'] = point_lst_insert_skip_realx_scale_skipadjust
    pass

#[解析层MAIN step5]:在point_lst_insert_skip_realx_scale_skipadjust基础上计算真实坐标，完成对y的转换
def cal_real_coord_y():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:
        real_draw_coord = []
        y_base_value    = WAVE_ORIGIN_STARTY + WAVE_HEIGHT * (1+WAVE_DICT['sig_index'])
        for point in WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust']:
            point_adjust = 0
            if(point[1] == 0):
                point_adjust = y_base_value -30
            elif(point[1] == 1):
                point_adjust = y_base_value -70
            elif(point[1] == 2):
                ###!!!还需要改
                if(WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'][WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'].index(point)-1][1]==1):
                    point_adjust = y_base_value -70
                else:
                    point_adjust = y_base_value -30
            elif(point[1] == 2.5):
                if(WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'][WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'].index(point)-2][1]==1):#下一个值
                    point_adjust = y_base_value -70
                else:
                    point_adjust = y_base_value -30                    
            else:
                point_adjust = y_base_value -50
            real_draw_coord.append([point[0],point_adjust])
        WAVE_DICT['real_draw_coord'] = real_draw_coord    
    pass

#[绘图层MAIN]:在real_draw_coord基础上绘制
def cal_real_coord_draw():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:
        for i in range(len(WAVE_DICT['real_draw_coord'])-1):
            start_point = WAVE_DICT['real_draw_coord'][i]
            end_point   = WAVE_DICT['real_draw_coord'][i+1]
            if(WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'][i][1] !=2):
                svg_draw_meshline(start_point,end_point,WAVE_DICT['sig_color'],WAVE_DICT['sig_linewidth'])
            if(WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'][i][1] == 2 or WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'][i][1] == 2.5):
                #需要补充，绘制skip线段
                pass
    pass

#[MISC]：初始波形点插值、相对时间变成绝对时间
def sigline_to_pointslst(sig_lines):#
    #时间累加
    for i in range(len(sig_lines)):
        if(i!=0):
            sig_lines[i][0] += sig_lines[i-1][0]
    inserted_sig_lines=list(range(2*len(sig_lines)))
    for i in range(len(sig_lines)):
        inserted_sig_lines[2*i] = sig_lines[i]
        if(i!=0):#inser
            inserted_sig_lines[2*i-1] = [inserted_sig_lines[2*i][0],inserted_sig_lines[2*i-2][1]] #时间取后一个的，数值取前一个的        
    inserted_sig_lines[-1] = [END_TIME,inserted_sig_lines[-2][1]]
    return inserted_sig_lines

#获取第i个波形的坐标原点，i从0开始
def get_axis_start_point(index):
    return  (WAVE_ORIGIN_STARTX,WAVE_ORIGIN_STARTY+WAVE_HEIGHT*(index+1))

def cor_convert(points_lst,sig_index):#坐标变换，变换为图形坐标,这里还没有支持模糊量，可以设置为0.5,以及scale信息
    output_point_lst=[]
    for point in points_lst:
        #output_point_lst.append((int(point[0]*SCALE)+get_axis_start_point(sig_index)[0],get_axis_start_point(sig_index)[1]-20-60*point[1]))
        output_point_lst.append(((point[0]*SCALE)+get_axis_start_point(sig_index)[0],get_axis_start_point(sig_index)[1]-20-60*point[1]))

    return output_point_lst

def cor_convert_skip_lst():#skip_lst坐标变换
    global SKIP_LST
    output_section_lst=[]
    for section in SKIP_LST:
        #output_section_lst.append([int(section[0]*SCALE)+WAVE_ORIGIN_STARTX,int(section[1]*SCALE)+WAVE_ORIGIN_STARTX])
        output_section_lst.append([(section[0]*SCALE)+WAVE_ORIGIN_STARTX,(section[1]*SCALE)+WAVE_ORIGIN_STARTX])
    return output_section_lst
    
#[绘图层]：根据2点绘制水平或垂直直线
def svg_draw_meshline(start_point,end_point,color,line_width):
    MODE = None
    x1,y1   =   start_point
    x2,y2   =   end_point
    
    if(x1==x2):
        MODE = "V"
    elif(y1==y2):
        MODE = "H"
    else:
        print("ERROR in svg_draw_meshline")
        return
        
    if(MODE == "V"):
        if(y2>y1):
            # y1 = y1 - int(line_width/2)
            # y2 = y2 + int(line_width/2)
            y1 = y1 - (line_width/2)
            y2 = y2 + (line_width/2)
        if(y2<y1):
            # y1 = y1 + int(line_width/2)
            # y2 = y2 - int(line_width/2)  
            y1 = y1 + (line_width/2)
            y2 = y2 - (line_width/2)         
    if(MODE == "H"):
        if(x2>x1):
            # x1 = x1 - int(line_width/2)
            # x2 = x2 + int(line_width/2) 
            x1 = x1 - (line_width/2)
            x2 = x2 + (line_width/2)    
        if(x2<x1):
            # x1 = x1 + int(line_width/2)
            # x2 = x2 - int(line_width/2) 
            x1 = x1 + (line_width/2)
            x2 = x2 - (line_width/2)                 

    print('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke={} stroke-width="{}" /> <!-- SIG -->'.format(x1,y1,x2,y2,color,line_width))

#[绘图层] [skip] :绘制skip左右短线
def svg_draw_skipline(section_start,section_end,color,line_width):
    #draw left  skipline
    svg_draw_meshline((section_start[0],section_start[1]-10),(section_start[0],section_start[1]+10),color,line_width)
    #draw right skipline
    svg_draw_meshline((section_end[0],section_end[1]-10),(section_end[0],section_end[1]+10),color,line_width)

#[绘图层] [skip]:绘制包含skip区间的波形
def svg_draw_skip(start_point,section_start,section_end,end_point,color,line_width):#根据给定的4点绝对地址绘制SKIP
    svg_draw_meshline(start_point,section_start,color,line_width)
    svg_draw_skipline(section_start,section_end,color,line_width)
    svg_draw_meshline(section_end,end_point,color,line_width)
    
#[绘图层] [skip]:skip图形调整，在图像上，将skip后面的点集提前
def skip_points_adjust(point_lst,section_start,section_end):#禁止skip中有跳变
    output_point_lst=[]
    for point in point_lst:
        if(point[0]<=section_start):
            output_point_lst.append(point)
        else:#point[0]>section_end
            diff=point[0]-section_end
            output_point_lst.append((section_start+SKIP_LEN+diff,point[1]))
    return output_point_lst

def sum_compress(skip_num_acc,skip_lst_cor):
    result = 0
    for i in range(skip_num_acc):
        result += skip_lst_cor[i][1]-skip_lst_cor[i][0]
    return result

#[绘图层] :按顺序连接点集，包含skip处理 
def svg_draw_meshline_successive(point_lst,color,line_width):
    line_num            = len(point_lst) -1
    point_lst_forpaint  = point_lst
    skip_num_acc        = 0
    for i in range(line_num):
        #print(point_lst_forpaint)
        #规定skip区间之间不能有用户定义的跳变
        start_point = point_lst[i]
        end_point   = point_lst[i+1]   
        Flag_in_skip      = False
        skip_lst_cor = cor_convert_skip_lst()
        #判断是否含skip，用实际值进行判断
        for section in skip_lst_cor:
            if(start_point[0]<=section[0] and section[1]<=end_point[0]):#含有skip
                skip_num_acc += 1
                #检测到skip
                point_lst_forpaint=skip_points_adjust(point_lst_forpaint,section[0],section[1])
                section_end_adjust      = section[1] + SKIP_LEN*skip_num_acc - sum_compress(skip_num_acc,skip_lst_cor)
                section_start_adjust    = section_end_adjust - SKIP_LEN
                #更新绘图值
                start_point_p = point_lst_forpaint[i]
                end_point_p   = point_lst_forpaint[i+1]
                svg_draw_skip(start_point_p,(section_start_adjust,start_point_p[1]),(section_end_adjust,end_point_p[1]),end_point_p,color,line_width)
                #print(start_point_p,(section_start_adjust,start_point_p[1]),(section_end_adjust,end_point_p[1]),end_point_p,color,line_width)
                Flag_in_skip      = True
                break

        if(Flag_in_skip == False):
            pass
            start_point_p = point_lst_forpaint[i]
            end_point_p   = point_lst_forpaint[i+1]
            svg_draw_meshline(start_point_p,end_point_p,color,line_width)
        
        


def svg_draw_axis_mesh():
    pass

#[绘图层]：绘制x轴，包含skip处理
def svg_draw_axis_main(points_lst,sig_index):
    #提取起点和终点
    y_value     = get_axis_start_point(sig_index)[-1]
    start_point = get_axis_start_point(sig_index)
    end_point   = (points_lst[-1][0],y_value)
    skip_lst_cor = cor_convert_skip_lst()
    expand_point_lst=[start_point]
    for i in range(len(skip_lst_cor)):
        section = skip_lst_cor[i]
        expand_point_lst+=[(section[0],y_value),(section[1],y_value)]
    expand_point_lst.append(end_point)

    svg_draw_meshline_successive(expand_point_lst,"#000000",4)
    

def svg_draw_axis(points_lst,sig_index):
    #绘制x轴
    svg_draw_axis_main(points_lst,sig_index)
    #绘制网格
    svg_draw_axis_mesh()

#[绘图层]：主函数，绘制bin波形
def draw_sig(sig_lines,sig_manner,sig_color,sig_linewidth,sig_index):
    sig_lines_eval=[]
    for str_num in sig_lines:
        sig_lines_eval.append([eval(str_num[0]),eval(str_num[1])])
    points_lst=sigline_to_pointslst(sig_lines_eval,sig_index)
    points_lst=cor_convert(points_lst,sig_index)#坐标变换
    
    #print(points_lst)
    if(sig_manner == "bin"):
        svg_draw_meshline_successive(points_lst,sig_color,eval(sig_linewidth))
    
    #绘制带skip处理的坐标轴和网格
    svg_draw_axis(points_lst,sig_index)

#[解析层]：主函数
def cdw_parse_sig(lines):
    global END_TIME
    global SCALE
    global SKIP_LST
    Flag_in_sig      = False
    Sig_line_buffer  = []
    (signame,sig_manner,sig_color,sig_linewidth)=(None,None,None,None)
    sig_index        = 0
    
    for line in lines:
        element_lst = line.split()
        
        #print(element_lst)
        #寻找全局控制信号
        if(len(element_lst) >= 2):
            #找出ENDTIME
            if  (element_lst[0] == '@end'   ):
                END_TIME = eval(element_lst[1])
            #找出SCALE
            elif(element_lst[0] == '@scale' ):
                SCALE    = eval(element_lst[1])
            #找出SKIP
            elif(element_lst[0] == '@skip'  ):
                SKIP_LST.append([eval(element_lst[1]),eval(element_lst[-1])])
                
        
            
        if(Flag_in_sig == True):
            if(len(element_lst)!=2):#退出
                Flag_in_sig = False
                draw_sig(Sig_line_buffer,sig_manner,sig_color,sig_linewidth,sig_index)
                Sig_line_buffer=[]
                sig_index += 1
            else:#中间
                Sig_line_buffer.append(element_lst)
                
        if(len(element_lst) == 4):
            if(element_lst[1] in SIG_MANNER):#进入
                
                (signame,sig_manner,sig_color,sig_linewidth)=(element_lst[0][1:],element_lst[1],element_lst[2],element_lst[3])
                #print(signame,sig_manner,sig_color,sig_linewidth)
                Flag_in_sig = True
        
    pass

lines=get_lines()
get_args(lines)
get_wave(lines)
cal_skip_insert()
cal_real_coord_x()
cal_real_coord_x_scale()
cal_real_coord_x_scale_skipadjust()
cal_real_coord_y()
cal_real_coord_draw()
for wavedict in WAVE_LST:
    for elem in wavedict.items():
        print(elem)
# point_lst = [(200,280),(300,280),(300,220),(400,220),(400,280),(500,280)]
# svg_draw_meshline_successive(point_lst,SIG_GREEN,4)