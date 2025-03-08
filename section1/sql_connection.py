import sqlalchemy, json
from sqlalchemy import text
# need to pip install mysql-connector-python

class sql_alchemy():

    def __init__(self, db):
        with open('DB_Params.json', 'r') as file:
            self.__host = json.load(file)
        self.__db = db
        self.sp_params = dict()
        self.__alchemy_openSqlConnection()


    def __alchemy_openSqlConnection(self):
        try:
            self.__connection = 'mysql+mysqlconnector://{}:{}@{}:{}/{}'.format( self.__host['SQL']['user'],
                                                                                self.__host['SQL']['password'],
                                                                                self.__host['SQL']['name'],
                                                                                self.__host['SQL']['port'],
                                                                                self.__db )
            self.engine = sqlalchemy.create_engine(self.__connection,   future=True, pool_reset_on_return='rollback')
            
            self._alchemy_cnx = self.engine.connect()
        except Exception as error:
            print("ERROR MYSQL: {}".format(error))
            raise Exception(error)
        

    #to combine that function and delete that one...
    def call_sp(self, sp_name, data):
        try:
            if not sp_name in self.sp_params:
                self.__sp_get_params(sp_name)

            params = ', '.join([':'+param for param in self.sp_params[sp_name]]   )
            sp_query = text(f'CALL {sp_name}({params})')
            params_values = {   param: value for param, value in zip(self.sp_params[sp_name], data)  }

            self._alchemy_cnx.execute(sp_query, params_values)
            return 
        except Exception as e:
            raise Exception(e)


    def call_sp_with_output(self, sp_name, data, outParam='p_stock_id'):
        try:
            if not sp_name in self.sp_params:
                self.__sp_get_params(sp_name)
            
            #   Remove the p_InsertedID OUT param from this list
            if outParam in self.sp_params[sp_name]:
                self.sp_params[sp_name].remove(outParam)

            params = ', '.join([':'+param for param in self.sp_params[sp_name]]   )
            sp_query = text(f'CALL {sp_name}({params}, @{outParam})')
            
            params_values = {   param: value for param, value in zip(self.sp_params[sp_name], data)  }
            self._alchemy_cnx.execute(sp_query, params_values)
            inserted_id = self._alchemy_cnx.execute(text(f"SELECT @{outParam}")).fetchone()[0]

            return inserted_id
        except Exception as e:
            raise Exception(e)
        

    def __sp_get_params(self, sp_name):
        query = f"SELECT distinct(PARAMETER_NAME) FROM information_schema.parameters WHERE SPECIFIC_NAME = '{sp_name}' AND SPECIFIC_SCHEMA = '{self.__db}'"
        result = self._alchemy_cnx.execute(text(query))
        self.sp_params[sp_name] = [row[0] for row in result]
        if not self.sp_params[sp_name]:
            raise Exception(f"No parameters found for stored procedure: {sp_name}")


    def _commit(self):
        self._alchemy_cnx.commit()