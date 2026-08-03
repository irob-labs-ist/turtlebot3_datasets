# Migração do turtlebot_datasets de ROS 1 para ROS 2

Este documento serve para explicar todas as modificações realizadas e todos os ficheiros criados durante a migração do turtlebot_datasets 
de ROS 1 (Noetic) para ROS 2 (Humble/Iron).

---

######## Contexto geral da migração

O ROS 2 representa uma reescrita substancial do ROS 1 e não é compatível com ele ao nível de 
ferramentas, sistema de build, formato de bags, APIs Python, nem sistema de lançamento de nós. Migrar um pacote implica atualizar praticamente todas as camadas do projeto: metadados, compilação, comunicação, scripts e documentação.


######## Ficheiros modificados

### 1. CMakeLists.txt

**O que mudou:**
- cmake_minimum_required(VERSION 2.8.3) -> cmake_minimum_required(VERSION 3.5), versão mínima exigida pelo ament_cmake.
- Removida toda a lógica catkin: find_package(catkin REQUIRED), catkin_package(), variáveis ${catkin_INCLUDE_DIRS}, ${CATKIN_PACKAGE_BIN_DESTINATION}, etc.
- Adicionados find_package(ament_cmake REQUIRED) e find_package(ament_cmake_python REQUIRED) — ferramentas equivalentes no ROS 2.
- Adicionado ament_python_install_package(${PROJECT_NAME}) para instalar o módulo Python turtlebot_datasets/.
- Adicionados install() explícitos para scripts, ficheiros de lançamento, dados e configurações — no ROS 2 não existem variáveis automáticas de destino como no catkin.
- Adicionado ament_package() no fim — macro obrigatória no ROS 2 equivalente ao papel que catkin_package() tinha no ROS 1.

O sistema de build do ROS 2 é o ament_cmake, que é incompatível com o catkin.

---

### 2. package.xml

**O que mudou:**
- format="2" -> format="3". O formato 3 é o padrão do ROS 2 e introduz a tag <depend> que unifica build_depend + exec_depend, bem como suporte explícito a <buildtool_depend>ament_cmake</buildtool_depend>.
- Adicionado XML Schema para validação: <?xml-model href="http://download.ros.org/schema/package_format3.xsd" ...>.
- Removido <buildtool_depend>catkin</buildtool_depend>.
- Adicionados <buildtool_depend>ament_cmake</buildtool_depend> e <buildtool_depend>ament_cmake_python</buildtool_depend>.
- Adicionadas dependências de runtime ROS 2: rclpy, tf2_ros, tf2_msgs, geometry_msgs, sensor_msgs, nav_msgs, rosbag2_py, rosbag2_storage, ros2bag, rosbag2_transport, turtlebot3_bringup.
- Atualizado o bloco <export> com <build_type>ament_cmake</build_type>, necessário para que se identifique o tipo de build corretamente.

O package.xml foi atualizado para declarar as novas dependências ROS 2.

---

### 3. launch/turtlebot_playbag.launch.py (substitui o launch file antigo)

**O que mudou:**
- O ficheiro XML turtlebot_playbag.launch foi substituído por um ficheiro Python turtlebot_playbag.launch.py.
- <arg name="model"/> e <arg name="bag_name"/> -> DeclareLaunchArgument(...) com valores por defeito e descrições.
- <include file="$(find turtlebot3_bringup)/launch/turtlebot3_remote.launch"> -> IncludeLaunchDescription(PythonLaunchDescriptionSource([...])) usando FindPackageShare.
- <param name="/use_sim_time" value="true"/> (global, ROS 1) -> parameters=[{'use_sim_time': True}] em cada nó individualmente.
- <node pkg="rosbag" type="play" .../> -> ExecuteProcess(cmd=['ros2', 'bag', 'play', '--clock', bag_path]).
- <node pkg="rviz" type="rviz" .../> -> Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_config], parameters=[{'use_sim_time': True}]).
- Adicionados blocos comentados para map server (nav2), AMCL, EKF e publish_initial_tf, prontos a descomentar pelos estudantes.

O ROS 2 abandonou completamente o formato XML para ficheiros de lançamento. Os ficheiros .launch.py são scripts Python agora. 
Além disso, use_sim_time passou a ser um parâmetro por nó (não global), e o rosmaster foi substituído pelo DDS, ou seja roscore já não existe.

---

### 4. scripts/fix_stamps.py

**O que mudou:**
- Linha de shebang: #!/usr/bin/env python2.7 -> #!/usr/bin/env python3.
- Removidos: import rospy, import rosbag, import tf as tfros.
- Adicionados: import rosbag2_py, from rclpy.serialization import deserialize_message, serialize_message, from rclpy.time import Duration, from rosidl_runtime_py.utilities import get_message.
- A abertura do bag passou de rosbag.Bag(open(...), mode='r') para rosbag2_py.SequentialReader() com StorageOptions e ConverterOptions.
- A escrita passou de rosbag.Bag(open(...), mode='w') para rosbag2_py.SequentialWriter().
- O loop de leitura passou de for topic, msg, t in in_bag.read_messages() para while reader.has_next(): topic, raw_data, bag_ts_ns = reader.read_next(), seguido de deserialize_message(raw_data, MsgClass).
- O tipo de mensagem TF passou de tf/tfMessage para tf2_msgs/TFMessage — os campos são compatíveis mas o nome do tipo mudou.
- A aritmética de timestamps passou de rospy.Duration(offset) para aritmética direta em nanosegundos inteiros (o ROS 2 usa int nanosegundos em vez de float segundos).

O formato de bag do ROS 2 é completamente diferente. O ROS 2 usa rosbag2_py não ficheiros .bag. 

---

### 5. scripts/download_dataset.sh

**O que mudou:**
- rospack find turtlebot_datasets -> ros2 pkg prefix --share turtlebot_datasets, o equivalente ROS 2 para localizar a dirétoria partilhado de um pacote.
Adicionado fallback para quando o pacote ainda não está instalado.
- Adicionado passo de conversão automática: após extrair o .tar.gz, o script percorre todos os ficheiros .bag encontrados e executa rosbags-convert --src ... --dst ... para os converter para o formato rosbag2.
- Adicionadas mensagens de ajuda sobre como reproduzir o bag convertido com ros2 bag play.

O rospack não existe no ROS 2, foi substituído pelo ros2 pkg. Mais importante: os ficheiros .bag do ROS 1 não são legíveis pelo ros2 bag play. 
É obrigatório convertê-los para o formato rosbag2 antes de os poder usar. A ferramenta rosbags-convert (pacote Python rosbags) faz a conversão e traduz 
também os tipos de mensagens (e.g., tf/tfMessage para tf2_msgs/TFMessage).

---

### 6. README.md

**O que mudou:**
- Substituída toda a secção "Steps" com instruções ROS 2:
  - sudo apt install python-pip -> sudo apt install python3-pip python3-rosbag2 ros-$ROS_DISTRO-rosbag2 ...
  - git clone ... && catkin_make && source ~/.bashrc -> colcon build --packages-select turtlebot_datasets && source install/setup.bash
  - roscd turtlebot_datasets/scripts && bash download_dataset.sh -> bash scripts/download_dataset.sh (sem roscd)
  - rosrun turtlebot_datasets publish_initial_tf.sh odom -> ros2 run turtlebot_datasets publish_initial_tf -- odom
  - roslaunch turtlebot_datasets turtlebot_playbag.launch -> ros2 launch turtlebot_datasets turtlebot_playbag.launch.py
  - rosbag info -> ros2 bag info
  - rosbag play --clock -> ros2 bag play --clock

- Secção "Notices" atualizada: substituída a explicação de rosparam set use_sim_time true + roscore pela explicação do parâmetro por nó e da ausência de master no ROS 2.
- Atualizado o tipo de mensagem TF de tf/tfMessage para tf2_msgs/msg/TFMessage.
- Adicionada secção sobre QoS (inexistente no ROS 1) explicando a necessidade de compatibilidade de perfis entre publishers e subscribers.
- Adicionada secção Fixing stamp offsets adaptado corretamente para o novo fix_stamps.py (diretórios em vez de ficheiros).
- Referência ao rosrun tf2_tools view_frames.py atualizada para ros2 run tf2_tools view_frames.

Todos os comandos ROS 1 são inválidos no ROS 2.

---

######## Ficheiros novos criados

- setup.py

Define o pacote Python turtlebot_datasets para o colcon e para o pip.
Lista os data_files a instalar (ficheiros de lançamento, configurações, dados, etc.) e declara o entry_point e publish_initial_tf, que torna o comando ros2 run turtlebot_datasets publish_initial_tf disponível após o build.
Adicionada opção para correr com rviz2 ou com foxglove (publica o nó e abre a versão web, é necessário colocar ws://localhost:8765 no site)
Esta opção é ativada como parametro:

ros2 launch turtlebot_datasets turtlebot_playbag.launch.py viz:=foxglove
ros2 launch turtlebot_datasets turtlebot_playbag.launch.py viz:=rviz2

No ROS 2 com ament_cmake_python, o setup.py é obrigatório para que o colcon saiba como instalar o módulo Python e os seus recursos associados.
No ROS 1 com catkin, os scripts eram simplesmente copiados, no ROS 2 são instalados como um pacote Python com entry points.

---


- setup.cfg
Configura as dirétorias de instalação dos scripts Python gerados pelo setup.py. 

---


- resource/turtlebot_datasets (ficheiro vazio)

Marcador do índice ament. É um ficheiro vazio cujo nome corresponde ao nome do pacote, colocado em resource/. 
O ament_index (equivalente ao rospack do ROS 1) usa este ficheiro para registar e descobrir o pacote no sistema.

O ROS 2 usa um sistema de índice de pacotes diferente do ROS 1. 
Sem este marcador, ros2 pkg list e ros2 pkg prefix não encontram o pacote, e qualquer tentativa de usar ros2 run ou ros2 launch com este pacote falha.

---


- turtlebot_datasets/__init__.py (ficheiro vazio)

Torna a dirétoria turtlebot_datasets/ num módulo Python importável. 
Permite que os outros ficheiros do pacote (como publish_initial_tf.py e qos_profiles.py) sejam importados com from turtlebot_datasets.qos_profiles import SENSOR_QOS.
Sem este ficheiro, o Python não reconhece a dirétoria como um módulo e os imports falham.

---


- turtlebot_datasets/publish_initial_tf.py (substitui o publish_initial_tf em scripts)

Substitui o script bash scripts/publish_initial_tf.sh. 
É um nó rclpy que publica a transformação estática mocap -> <fixed_frame> no tópico /tf_static, com QoS TRANSIENT_LOCAL .

Aceita o nome do frame fixo como argumento de linha de comandos (e.g., odom, map).
Cria um TransformStamped com os valores medidos no início do dataset.
Publica uma única mensagem TFMessage em /tf_static com durabilidade TRANSIENT_LOCAL, garantindo que qualquer subscriber que se ligue depois (incluindo o rviz2) recebe a mensagem imediatamente.

O ROS 2 requer que os publishers estáticos de TF usem QoS TRANSIENT_LOCAL
sem isso, subscribers que se liguem após a publicação nunca recebem a transformação. 
Um script com ros2 run tf2_ros static_transform_publisher também funcionaria, mas um nó Python integrado no pacote é mais fácil de incorporar no ficheiro de lançamento como um nó.

---


- turtlebot_datasets/qos_profiles.py

Define perfis de QoS (Quality of Service) reutilizáveis para os nós deste pacote:
- STATIC_TF_QOS — para /tf_static: TRANSIENT_LOCAL + RELIABLE, garante entrega a subscribers tardios.
- SENSOR_QOS — para /scan, /imu, /odom, /image: BEST_EFFORT, corresponde ao perfil por defeito dos publishers de sensores.
- NAV_QOS — para odometria e navegação
- DEFAULT_QOS — QoS padrão RELIABLE do ROS 2.

Uma das mudanças mais impactantes do ROS 2 face ao ROS 1 é a introdução de QoS explícito. 
No ROS 1, toda a comunicação era TCP fiável. 
no ROS 2, publishers e subscribers têm de concordar no perfil de QoS (fiabilidade, durabilidade, histórico). 
Uma incompatibilidade de QoS não gera erro, simplesmente não há comunicação, o que é difícil de diagnosticar. 
Centralizar os perfis num ficheiro partilhado evita inconsistências e facilita a depuração pelos estudantes.

---


- config/rviz2_config.rviz

Ficheiro de configuração do RViz2 com os seguintes displays pré-configurados:

- Grid — grelha de referência no plano XY.
- RobotModel — modelo 3D do Turtlebot3, subscrito de /robot_description.
- LaserScan — scan laser em /scan com QoS BEST_EFFORT.
- TF — visualização da árvore de frames de coordenadas.
- Odometry — setas de odometria em /odom com QoS BEST_EFFORT.

Opcional para adicionar. podemos incluir ou não e os alunos podem alterar se quiserem deixar permanentes algumas alterações às configs do rviz2.






