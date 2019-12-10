import olympe
from olympe.messages.ardrone3.Piloting import TakeOff, Landing, moveBy
import olympe_deps as od

drone = olympe.Drone("192.168.42.1", drone_type=od.ARSDK_DEVICE_TYPE_BEBOP_2)
drone.connection()
drone(TakeOff()).wait()
drone(moveBy(1,0,0,0)).wait()
drone(Landing()).wait()
drone.disconnection()



drone(moveBy(0,0,1,0)).wait()
drone(Landing()).wait()
drone.disconnection()