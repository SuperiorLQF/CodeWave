#new feature:bin和clk类型的逻辑操作
# parameter
# param_color
import sys
SKIP_LST                =   []
SCALE                   =   1
SIG_MANNER              =   ['bin','sig','clk','combine']
SIG_GREEN               =   "#229933"
WAVE_HEIGHT             =   100
WAVE_ORIGIN_STARTX      =   300
WAVE_ORIGIN_STARTY      =   200 
ORIGIN_POINT            =   (WAVE_ORIGIN_STARTX,WAVE_ORIGIN_STARTY)
END_TIME                =   0
SKIP_LEN                =   20
WAVE_LST                =   []
DIGIT_OPEN              =   True

CDW_FILE_NAME           =   'wavecode.cdw'

#[解析层MAIN]：读取文件存入列表
def get_lines():
    # 打开文件  
    global CDW_FILE_NAME
    with open(CDW_FILE_NAME, 'r' ,encoding='UTF-8') as file:  
        # 读取所有行  
        lines = file.readlines()  

    return lines

#[解析层MAIN]：获取参数
def get_args(lines):
    global END_TIME,SCALE,SKIP_LST,DIGIT_OPEN
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
            #找出DIGIT
            elif(element_lst[0] == '@digit' ):
                DIGIT_OPEN = eval(element_lst[1])

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
            if(len(element_lst)<2):#退出
                #插入点处理，目前的坐标还是时间坐标，value也还是1和0
                if(WAVE_DICT['sig_manner']=='bin'):#累加且插值
                    WAVE_DICT['point_lst_insert']=sigline_to_pointslst(WAVE_DICT['point_lst'],1)
                elif(WAVE_DICT['sig_manner']=='clk' or WAVE_DICT['sig_manner']=='combine'):#不累加插值
                    WAVE_DICT['point_lst_insert']=sigline_to_pointslst(WAVE_DICT['point_lst'],2)
                else:#累加不插值
                    WAVE_DICT['point_lst_insert']=sigline_to_pointslst(WAVE_DICT['point_lst'],3)

                WAVE_LST.append(WAVE_DICT.copy()) 
                #后处理
                Flag_in_sig = False
                WAVE_DICT   = {}
                sig_index += 1
            else:#中间
                if(WAVE_DICT['sig_manner']=='bin'):
                    WAVE_DICT['point_lst'].append([eval(element_lst[0]),eval(element_lst[1])])
                elif(WAVE_DICT['sig_manner']=='sig'):
                    WAVE_DICT['point_lst'].append([eval(element_lst[0]),element_lst[1]])
                elif(WAVE_DICT['sig_manner']=='clk'):
                    T=eval(element_lst[0][2:])
                    rate=eval(element_lst[1][5:])
                    offset=eval(element_lst[2][7:])
                    pos_point_x = offset
                    if(offset == 0):
                        pass
                    else:
                        WAVE_DICT['point_lst'].append([0,0])
                    while(pos_point_x<END_TIME):
                        WAVE_DICT['point_lst'].append([pos_point_x,1])
                        neg_point_x= pos_point_x + T*rate
                        if(neg_point_x>=END_TIME):
                            break
                        else:
                            WAVE_DICT['point_lst'].append([neg_point_x,0])
                        pos_point_x = neg_point_x + T*(1-rate)
                    # print("HAHA")
                    # print(WAVE_DICT['point_lst'])
                elif(WAVE_DICT['sig_manner']=='combine'):
                    expression=element_lst[1:]
                    op1,op2,op=parse_expression(expression)
                    WAVE_DICT['point_lst']=combine_logic_point_lst(op1,op2,op)[:]
                    submanner1,submanner2= parse_submanner(op1),parse_submanner(op2)
                    if(submanner1 =='clk' or submanner2 == 'clk'):
                        WAVE_DICT['sub_manner'] = 'clk'
                    else:
                        WAVE_DICT['sub_manner'] = 'bin'
                else:
                    pass
                
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
        if(True):
            point_lst_real_coord=[]
            point_lst_real_coord.append(WAVE_DICT['point_lst_insert'][0])#point
            for point_index in range(0,len(WAVE_DICT['point_lst_insert'])-1):
                for section in SKIP_LST:
                    skip_start = section[0]
                    skip_end   = section[1]
                    if(skip_start>=WAVE_DICT['point_lst_insert'][point_index][0] and skip_start<=WAVE_DICT['point_lst_insert'][point_index+1][0]):
                        point_lst_real_coord.append([section[0],2])#section start
                        point_lst_real_coord.append([section[1],2.5])#section end
                point_lst_real_coord.append(WAVE_DICT['point_lst_insert'][point_index+1])#point

            #保证skip中的点不显示
            point_lst_real_coord_m =[]
            MAX=0
            for point in point_lst_real_coord:
                if(point[0]>=MAX):
                    point_lst_real_coord_m.append(point)
                    MAX = point[0]
            WAVE_DICT['point_lst_insert_skip'] = point_lst_real_coord_m
        else:
            WAVE_DICT['point_lst_insert_skip'] = WAVE_DICT['point_lst_insert']
        
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
        if(WAVE_DICT['sig_manner']=='bin' or WAVE_DICT['sig_manner']=='clk' or WAVE_DICT['sig_manner']=='combine'):
            real_draw_coord = []
            y_base_value    = WAVE_ORIGIN_STARTY + WAVE_HEIGHT * (1+WAVE_DICT['sig_index'])
            point_adjust = 0
            for point in WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust']:
                if(point[1] == 0):
                    point_adjust = y_base_value -30
                elif(point[1] == 1):
                    point_adjust = y_base_value -70
                elif(point[1] == 2 or point[1] == 2.5):
                    point_adjust = point_adjust                  
                else:
                    point_adjust = y_base_value -50
                real_draw_coord.append([point[0],point_adjust])
            WAVE_DICT['real_draw_coord'] = real_draw_coord    
        else:
            real_draw_coord = []
            y_base_value    = WAVE_ORIGIN_STARTY + WAVE_HEIGHT * (1+WAVE_DICT['sig_index'])
            point_adjust = 0
            for point in WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust']:
                if(point[1] == 2 or point[1] == 2.5):
                    point_adjust = point_adjust
                else:
                    point_adjust = point[1]
                real_draw_coord.append([point[0],point[1],point_adjust])
            WAVE_DICT['real_draw_coord'] = real_draw_coord

    pass

#[解析层MAIN step6]:获取real_coord_y的x坐标点集
def cal_real_axis_x():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:
        y_base_value    = WAVE_ORIGIN_STARTY + WAVE_HEIGHT * (1+WAVE_DICT['sig_index'])
        real_axis_x = []
        for point in WAVE_DICT['real_draw_coord']:
            real_axis_x.append([point[0],y_base_value])
        WAVE_DICT['real_axis_x'] = real_axis_x   
    pass   

#[解析层MAIN step7]:获取x标度，根据real_axis_x和point_lst_insert_skip
def cal_time_note():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:
        point_lst_insert_skip   = WAVE_DICT['point_lst_insert_skip']
        point_lst_insert_skip_x= []
        point_lst_insert_skip_x_remove_redun = []
        for point in point_lst_insert_skip:
            point_lst_insert_skip_x.append(point[0])
        for i in point_lst_insert_skip_x:
            if(i not in point_lst_insert_skip_x_remove_redun):
                point_lst_insert_skip_x_remove_redun.append(i)

        real_axis_x             = WAVE_DICT['real_axis_x']
        real_axis_note_position = [[i[0],i[1]+10] for i in real_axis_x]
        real_axis_note_position_x = [i[0] for i in real_axis_note_position]
        real_axis_note_position_x_remove_redun = []
        for point in real_axis_note_position_x:
            if(point not in real_axis_note_position_x_remove_redun):
                real_axis_note_position_x_remove_redun.append(point)
        real_axis_note_position_xy_remove_redun =[]
        for i in real_axis_note_position_x_remove_redun:
            real_axis_note_position_xy_remove_redun.append([i,real_axis_note_position[0][-1]])

        time_note_dict = zip(point_lst_insert_skip_x_remove_redun,real_axis_note_position_xy_remove_redun)
        WAVE_DICT['time_note_dict'] = dict(time_note_dict).copy()  
    pass      

#[解析层MAIN step8]:获取mesh dot line位置，基于time_note_dict和point_lst_insert
def cal_real_mesh():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:
        output_lst=[]
        point_lst_insert_x=[point[0] for point in WAVE_DICT['point_lst_insert']]
        for key,value in WAVE_DICT['time_note_dict'].items():
            if(key in point_lst_insert_x):
                output_lst.append(value[0])
        WAVE_DICT['real_mesh_lst_x'] = output_lst[:]

#[绘图层MAIN step1]:绘制虚线，基于real_mesh_x_lst
def cal_real_mesh_draw():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:
        if(WAVE_DICT['sig_manner']=='bin' or (WAVE_DICT['sig_manner']=='combine' and WAVE_DICT['sub_manner']!='clk')):
            dash_end_y   = WAVE_DICT['real_axis_x'][0][-1]
            dash_start_y = dash_end_y -30
            for x in WAVE_DICT['real_mesh_lst_x']:
                if(x!=WAVE_DICT['real_mesh_lst_x'][0] and x!=WAVE_DICT['real_mesh_lst_x'][-1]):
                    #dash_start_y_modify = dash_start_y
                    x_index = WAVE_DICT['real_mesh_lst_x'].index(x)
                    y_point_lst = WAVE_DICT['point_lst'][x_index][1]
                    dash_start_y_modify = dash_end_y -30 - 40*y_point_lst 
                elif(x==WAVE_DICT['real_mesh_lst_x'][0]):
                    dash_start_y_modify =WAVE_DICT['real_draw_coord'][0][1]
                else:
                    dash_start_y_modify =WAVE_DICT['real_draw_coord'][-1][-1]
                print('<line x1="{}" y1="{}" x2="{}" y2="{}"  stroke="lightgrey" stroke-width="1" stroke-dasharray="10,5" /> <!-- dot mesh -->'.format(x,dash_start_y_modify,x,dash_end_y))
        #<line x1="201" y1="200" x2="201" y2="300"  stroke="lightgrey" stroke-width="2" stroke-dasharray="10,5" /> <!-- dot mesh -->
        elif(WAVE_DICT['sig_manner']=='clk' or WAVE_DICT['sig_manner']=='combine'):
            continue
        else:#!!!
            y_value_base= WAVE_ORIGIN_STARTY + WAVE_HEIGHT * (1+WAVE_DICT['sig_index'])
            y_value_up  = y_value_base -70
            y_value_down= y_value_base -30
            y_value_middle=y_value_base -50
            dash_end_y    = y_value_base
            dash_start_y  = y_value_middle
            for x in WAVE_DICT['real_mesh_lst_x']:
                if(x!=WAVE_DICT['real_mesh_lst_x'][0] and x!=WAVE_DICT['real_mesh_lst_x'][-1]):
                    dash_start_y_modify = dash_start_y
                elif(x==WAVE_DICT['real_mesh_lst_x'][0]):
                    dash_start_y_modify = dash_start_y
                else:
                    dash_start_y_modify = dash_start_y
                print('<line x1="{}" y1="{}" x2="{}" y2="{}"  stroke="lightgrey" stroke-width="1" stroke-dasharray="10,5" /> <!-- dot mesh -->'.format(x,dash_start_y_modify,x,dash_end_y))            

#[绘图层MAIN step2]:在real_draw_coord基础上绘制wave
def cal_real_coord_draw():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:
        if(WAVE_DICT['sig_manner']=='bin' or WAVE_DICT['sig_manner']=='clk' or WAVE_DICT['sig_manner']=='combine'):
            for i in range(len(WAVE_DICT['real_draw_coord'])-1):
                start_point = WAVE_DICT['real_draw_coord'][i]
                end_point   = WAVE_DICT['real_draw_coord'][i+1]
                if(WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'][i][1] !=2):
                    svg_draw_meshline(start_point,end_point,WAVE_DICT['sig_color'],WAVE_DICT['sig_linewidth'])
                if(WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'][i][1] == 2 or WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'][i][1] == 2.5):
                    svg_draw_line([start_point[0]+6,start_point[1]-10],[start_point[0]-6,start_point[1]+10],WAVE_DICT['sig_color'],WAVE_DICT['sig_linewidth'])

        elif(WAVE_DICT['sig_manner']=='sig'):
        #[[200, 'MODE1', 'MODE1'], [210, 'MODE2', 'MODE2'], [250, 'MODE3', 'MODE3'], [260, 'MODE4', 'MODE4'], [300, 2, 'MODE4'], [320, 2.5, 'MODE4'], [380, 2, 'MODE4'],
            for i in range(len(WAVE_DICT['real_draw_coord'])-1):
                start_point = WAVE_DICT['real_draw_coord'][i]
                end_point   = WAVE_DICT['real_draw_coord'][i+1]
                y_value_base= WAVE_ORIGIN_STARTY + WAVE_HEIGHT * (1+WAVE_DICT['sig_index'])
                y_value_up  = y_value_base -70
                y_value_down= y_value_base -30
                y_value_middle=y_value_base -50
                sig_start_point = [start_point,y_value_up,y_value_down]
                sig_end_point   = [end_point,y_value_up,y_value_down]
                #!!!
                if(end_point==WAVE_DICT['real_draw_coord'][-1]):
                    Flag_last = True
                else:
                    Flag_last = False
                if(start_point[1]==2.5):#/===
                    svg_draw_line([start_point[0]+6,y_value_up],[start_point[0]-6,y_value_down],'lightgrey',WAVE_DICT['sig_linewidth'],True)
                    svg_draw_sig(sig_start_point,sig_end_point,False,Flag_last,WAVE_DICT['sig_color'],WAVE_DICT['sig_linewidth'])
                elif(start_point[1]==2):#/
                    svg_draw_line([start_point[0]+6,y_value_up],[start_point[0]-6,y_value_down],'lightgrey',WAVE_DICT['sig_linewidth'],True)
                else:#><==
                    svg_draw_sig(sig_start_point,sig_end_point,True,Flag_last,WAVE_DICT['sig_color'],WAVE_DICT['sig_linewidth'])

#[绘图层MAIN step3]:在real_axis_x基础上绘制x轴
def cal_real_coord_draw_aixs_x():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:
        for i in range(len(WAVE_DICT['real_axis_x'])-1):
            start_point = WAVE_DICT['real_axis_x'][i]
            end_point   = WAVE_DICT['real_axis_x'][i+1]
            if(WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'][i][1] !=2):
                svg_draw_meshline(start_point,end_point,"#000000",1)
            if(WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'][i][1] == 2 or WAVE_DICT['point_lst_insert_skip_realx_scale_skipadjust'][i][1] == 2.5):
                svg_draw_line([start_point[0]+3,start_point[1]-5],[start_point[0]-3,start_point[1]+5],"#000000",1)
                pass
    pass

#[绘图层MAIN step4]:绘制阶跃点的时间标度，基于time_note_dict
def cal_time_note_draw():
    # <text x="0" y="5" fill="red">这是一段文本</text>
    global WAVE_LST
    if(DIGIT_OPEN == True):
        for WAVE_DICT in WAVE_LST:
            if(WAVE_DICT['sig_manner']=='clk' or (WAVE_DICT['sig_manner']=='combine' and WAVE_DICT['sub_manner']=='clk')):
                continue
            #!!!这里可以加入wave的 digital局部控制显示
            for time_str,point in WAVE_DICT['time_note_dict'].items():
                print('<text x="{}" y="{}" fill="#000000" font-size="{}" text-anchor="middle" dominant-baseline="central" transform="rotate(60,{},{})">{}</text>'.format(point[0],point[1],8,point[0],point[1],time_str))
    else:
        pass
    
#[绘图层MAIN step5]:绘制sig tag，基于real_draw_coord
def sig_tag_draw():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:  
        if(WAVE_DICT['sig_manner']=='sig'):
            y_base_value    = WAVE_ORIGIN_STARTY + WAVE_HEIGHT * (1+WAVE_DICT['sig_index'])
            y_value_middle  = y_base_value -50
            real_draw_coord=WAVE_DICT['real_draw_coord']
            for i in range(len(real_draw_coord)-1):
                start_point = real_draw_coord[i]
                end_point   = real_draw_coord[i+1]
                if(start_point[1]!=2 and start_point[1]!=2.5 and end_point[1]!=2 and end_point[1]!=2.5):
                    tag_inf     = [(start_point[0]+end_point[0])/2,y_value_middle,start_point[1]]
                    print('<text x="{}" y="{}" fill="#000000" font-size="{}" text-anchor="middle" dominant-baseline="central" transform="rotate(0,{},{})" font-weight="bold"  font-family="Consolas, monospace">{}</text>'.format(tag_inf[0],tag_inf[1],13,tag_inf[0],tag_inf[1],tag_inf[2]))
                elif(start_point[1]!=2 and start_point[1]!=2.5):
                    tag_inf     = [start_point[0]+SKIP_LEN,y_value_middle,start_point[1]] #[start_point[0]+SCALE,y_value_middle,start_point[1]]
                    print('<text x="{}" y="{}" fill="#000000" font-size="{}" text-anchor="start" dominant-baseline="central" transform="rotate(0,{},{})" font-weight="bold"  font-family="Consolas, monospace">{}</text>'.format(tag_inf[0],tag_inf[1],13,tag_inf[0],tag_inf[1],tag_inf[2]))


        else:
            pass  

#[绘图层MAIN step6]:绘制sig name
def sig_title_draw():
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:  
        signame = WAVE_DICT['sig_name']
        y_value_base=WAVE_ORIGIN_STARTY + WAVE_HEIGHT * (1+WAVE_DICT['sig_index'])
        text_complex=[WAVE_ORIGIN_STARTX-10,y_value_base-50,signame]
        print('<text x="{}" y="{}" fill="#000000" font-size="{}" text-anchor="end" dominant-baseline="central" transform="rotate(0,{},{})" font-weight="bold"  font-family="Consolas, monospace">{}</text>'.format(text_complex[0],text_complex[1],18,text_complex[0],text_complex[1],text_complex[2]))


#[MISC]：初始波形点插值、相对时间变成绝对时间
def sigline_to_pointslst(sig_lines,insert_flag=1):#
    #时间累加
    if(insert_flag !=2):
        for i in range(len(sig_lines)):
            if(i!=0):
                sig_lines[i][0] += sig_lines[i-1][0]
    if(insert_flag == 1 or insert_flag == 2):
        inserted_sig_lines=list(range(2*len(sig_lines)))
        for i in range(len(sig_lines)):
            inserted_sig_lines[2*i] = sig_lines[i]
            if(i!=0):#inser
                inserted_sig_lines[2*i-1] = [inserted_sig_lines[2*i][0],inserted_sig_lines[2*i-2][1]] #时间取后一个的，数值取前一个的        
        inserted_sig_lines[-1] = [END_TIME,inserted_sig_lines[-2][1]]
        if(insert_flag ==1):#开头加0
            return inserted_sig_lines
        else:
            return [[0,0]]+inserted_sig_lines
    else:
        return sig_lines+[[END_TIME,sig_lines[-1][1]]]

#[MISC]：逻辑运算,给出sig_name返回sig_manner
def parse_submanner(sig_name):
    global WAVE_LST
    for WAVE_DICT in WAVE_LST:     
        if(WAVE_DICT['sig_name']==sig_name):
            if(WAVE_DICT['sig_manner']=='combine'):
                return WAVE_DICT['sub_manner']
            else:
                return WAVE_DICT['sig_manner']
        
#[MISC]：逻辑运算,目前仅限2元和1元，多元请拆分
def combine_logic_point_lst(operator_name1,operator_name2,logic_operand):
    #使用示例：combine_logic_point_lst('V_SYNC','V_DE','or')
    global WAVE_LST
    operator_point_lst1=[]
    operator_point_lst2=[]
    for WAVE_DICT in WAVE_LST: 
        if(WAVE_DICT['sig_name']==operator_name1):
            if(WAVE_DICT['sig_manner']=='sig'):
                print('WRONG operator manner')
            else:
                operator_point_lst1 = WAVE_DICT['point_lst'][:]
                #print(WAVE_DICT)
        elif(WAVE_DICT['sig_name']==operator_name2):
            if(WAVE_DICT['sig_manner']=='sig'):
                print('WRONG operator manner')
            else:
                operator_point_lst2 = WAVE_DICT['point_lst'][:]
                #print(WAVE_DICT)

    output_point_lst = []
    operator_point_lst1_x = [point[0] for point in operator_point_lst1]
    operator_point_lst1_y = [point[1] for point in operator_point_lst1]
    operator_point_lst2_x = [point[0] for point in operator_point_lst2]
    operator_point_lst2_y = [point[1] for point in operator_point_lst2]

    operator_point_lst1_xy= [operator_point_lst1_x,operator_point_lst1_y]
    operator_point_lst2_xy= [operator_point_lst2_x,operator_point_lst2_y]
    operator_point_lst12_x= list(set(operator_point_lst1_x) | set(operator_point_lst2_x))#取公共部分
    operator_point_lst12_x= sorted(operator_point_lst12_x)
    #insert lst1
    inserted_lst1=[]
    i=0
    last_value=0
    for x in operator_point_lst12_x:
        if(x in operator_point_lst1_x):
            inserted_lst1.append([operator_point_lst1_x[i],operator_point_lst1_y[i]])
            last_value = operator_point_lst1_y[i]
            i=i+1
        else:
            inserted_lst1.append([x,last_value])
    
    #insert lst2
    inserted_lst2=[]
    i=0
    last_value=0
    for x in operator_point_lst12_x:
        if(x in operator_point_lst2_x):
            inserted_lst2.append([operator_point_lst2_x[i],operator_point_lst2_y[i]])
            last_value = operator_point_lst2_y[i]
            i=i+1
        else:
            inserted_lst2.append([x,last_value]) 
    
    #print(inserted_lst1)
    #print(inserted_lst2)
    #logic operation
    output_result_point_lst=[]
    len_lst1=len(inserted_lst1)
    len_lst2=len(inserted_lst2)
    if(len_lst1!=len_lst2):
        print('ERROR:combine_logic_point_lst error')
        return
    else:
        if(logic_operand == '~' or logic_operand == '!' or logic_operand == 'not'):
            for i in range(len_lst1):
                output_result_point_lst.append([inserted_lst1[i][0],1-inserted_lst1[i][1]])
                pass
        elif(logic_operand == '&' or logic_operand == 'and'):
            for i in range(len_lst1):
                output_result_point_lst.append([inserted_lst1[i][0],inserted_lst1[i][1] and inserted_lst2[i][1]] )
                pass
        elif(logic_operand == '|' or logic_operand == 'or'):
            for i in range(len_lst1):
                output_result_point_lst.append([inserted_lst1[i][0],inserted_lst1[i][1] or inserted_lst2[i][1]] )
                pass
        elif(logic_operand == '^' or logic_operand == 'xor'):
            for i in range(len_lst1):
                output_result_point_lst.append([inserted_lst1[i][0],inserted_lst1[i][1] ^ inserted_lst2[i][1]] )
                pass
        else:
            print("ERROR:wrong operand")
    # print(operator_point_lst1)
    # print(operator_point_lst2)
    # print(output_result_point_lst)
    return output_result_point_lst

#[MISC]：表达式分解
def parse_expression(expression):
    #print(expression,type(expression))
    if(len(expression)==2):
        op  = expression[0]
        op1 = expression[1]
        op2 = expression[1]
    else:
        op  = expression[1]
        op1 = expression[0]
        op2 = expression[2]
    return op1,op2,op

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


def svg_draw_line(start_point,end_point,color,line_width,dash=False):
    x1,y1   =   start_point
    x2,y2   =   end_point
    if(dash):
        print('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="{}" stroke-dasharray="10,5" /> <!-- dash -->'.format(x1,y1,x2,y2,color,line_width))
    else:
        print('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="{}" /> <!-- SIG -->'.format(x1,y1,x2,y2,color,line_width))


def svg_draw_sig(sig_start_point,sig_end_point,extend_flag,Flag_last,color,line_width):
    #sig start point [[[320, 2.5, 'MODE4']],y_up,y_down]
    x_start=sig_start_point[0][0]
    x_end  =sig_end_point[0][0]
    y_up=sig_end_point[1]
    y_down=sig_end_point[2]
    if(extend_flag == False):#/==
        if(sig_end_point[0][1]!=2):#short
            if(Flag_last):
                svg_draw_meshline([x_start+6,y_up],[x_end,y_up],color,line_width)
                svg_draw_meshline([x_start-6,y_down],[x_end,y_down],color,line_width)    
            else:            
                svg_draw_meshline([x_start+6,y_up],[x_end-6,y_up],color,line_width)
                svg_draw_meshline([x_start-6,y_down],[x_end-6,y_down],color,line_width)
            pass
        else:#long
            svg_draw_meshline([x_start+6,y_up],[x_end+6,y_up],color,line_width)
            svg_draw_meshline([x_start-6,y_down],[x_end-6,y_down],color,line_width) 
        ##!!!draw tag           
            pass
    else:#><=
        # ><
        if(x_start-6<WAVE_ORIGIN_STARTX):
            y_middle = (y_down+y_up)/2
            svg_draw_line([x_start,y_middle],[x_start+6,y_down],color,line_width)
            svg_draw_line([x_start,y_middle],[x_start+6,y_up],color,line_width)   
        else:         
            svg_draw_line([x_start-6,y_up],[x_start+6,y_down],color,line_width)
            svg_draw_line([x_start-6,y_down],[x_start+6,y_up],color,line_width)
        if(sig_end_point[0][1]!=2):#short
            if(Flag_last):
                svg_draw_meshline([x_start+6,y_up],[x_end,y_up],color,line_width)
                svg_draw_meshline([x_start+6,y_down],[x_end,y_down],color,line_width)  
            else:          
                svg_draw_meshline([x_start+6,y_up],[x_end-6,y_up],color,line_width)
                svg_draw_meshline([x_start+6,y_down],[x_end-6,y_down],color,line_width)
            pass
        else:#long          
            svg_draw_meshline([x_start+6,y_up],[x_end+6,y_up],color,line_width)
            svg_draw_meshline([x_start+6,y_down],[x_end-6,y_down],color,line_width)            
            pass   
        ##!!!draw tag     
        pass

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
        print("ERROR in svg_draw_meshline{},{}".format(start_point,end_point))
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

    print('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="{}" /> <!-- SIG -->'.format(x1,y1,x2,y2,color,line_width))

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

                Flag_in_sig = True
        
    pass
def print_HTML_head():
    print('<!DOCTYPE html>')
# <!DOCTYPE html>  
    print('<html>')
# <html>  
    print('<head>')
# <head>  
    print('\t<title>SVG Example</title>')
#     <title>SVG Example</title>
    print('<head>')  
# </head>  
    print('<body>')
# <body>    
    print('\t<svg width="10000" height="10000" >')
#     <svg width="10000" height="10000" > 
def print_HTML_tail():
    print('\t</svg>')
    print('</body>')
    print('</html>')




oldPrint = sys.stdout   # 用于后期还原
CDW_FILE_NAME = sys.argv[1]
#####################测试时可以注释###############################
output_html_file = open("codewave.html", "w")
sys.stdout = output_html_file
#####################测试时可以注释###############################

print_HTML_head()

lines=get_lines()
get_args(lines)
get_wave(lines)
cal_skip_insert()
cal_real_coord_x()
cal_real_coord_x_scale()
cal_real_coord_x_scale_skipadjust()
cal_real_coord_y()
cal_real_axis_x()
cal_time_note()
cal_real_mesh()

cal_real_mesh_draw()
cal_real_coord_draw()
cal_real_coord_draw_aixs_x()
cal_time_note_draw()
sig_tag_draw()
sig_title_draw()

print_HTML_tail()

sys.stdout = oldPrint  # 还原输出位置

for wavedict in WAVE_LST:
    for elem in wavedict.items():
        print(elem)
        pass
# point_lst = [(200,280),(300,280),(300,220),(400,220),(400,280),(500,280)]
# svg_draw_meshline_successive(point_lst,SIG_GREEN,4)