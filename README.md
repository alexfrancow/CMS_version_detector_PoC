# ML-wpver

Algunas páginas de Wordpress, Joomla, Drupal, etc. no ofrecen información de la versión por ningún lado, ni con herramientas somos capaces de sacar una versión, con esta herramienta gracias a los algoritmos de Machine Learning se podrá detectar una versión de cualquier CMS en base a una serie de clases.

## Quick start

Usamos el modelo randomforestmodel.pkl:

```
$ python3 ml-wpver.py -m test -u https://emetel.net/
```

Para generar un nuevo dataset:

```
$ python3 ml-wpver.py -gd 10000
```

Para generar y entrenar un nuevo modelo (se va a llamar randomforestmodel.pkl) y especificamos el dataset:

```
$ python3 ml-wpver.py -m train .csv
```


## Dataset

Las caracterísiticas de nuestro dataset serán los archivos de los que se compone el CMS WordPress, no todos.

Si nos vamos a la web: https://codex.wordpress.org/Current_events veremos los archivos que cambiaron en cada versión.

```
Ej:
En la 4.7.5 se modificaron los siguientes archivos:
wp-includes/class-wp-customize-manager.php
wp-includes/js/plupload/handlers.js
wp-includes/js/plupload/handlers.min.js
wp-includes/class-wp-xmlrpc-server.php
wp-includes/version.php
readme.html
wp-admin/about.php
wp-admin/includes/file.php
wp-admin/customize.php
wp-admin/js/updates.js
wp-admin/js/customize-controls.js
wp-admin/js/updates.min.js
wp-admin/js/customize-controls.min.js
```

Si nos descargamos esa versión y la anterior 4.7.4 y abrimos el archivo wp-includes/js/plupload/handlers.js:

<div style="text-align:center"><img src="images/1.png" /></div>

Vemos que las líneas cambian en ese archivo. Habría que descargar el listado total de archivos que han sido modificados o añadidos de sde la versión 0 hasta la última y comprobar cuantas líneas tienen los archivos .js o .css

Con python en lugar de contar las líneas vamos a contar los bytes de cada archivo .js o .css, solo los del lado del cliente ya que los .php no los vamos a poder visitar.

Primera prueba emetel.net vs be-sec.net:

```
https://emetel.net/ versión 4.9.11
https://www.be-sec.net/ versión 5.0.6
```

<p align="center"><img src="images/2.png" /></p>

Haremos una comprobación más grande antes de seguir:
En estas URLs tenemos 3 versiones que son iguales, y justamente da el mismo número de bytes en sus archivos:

<div style="text-align:center"><img src="images/3.png" /></div>

Dado que la API de wappalyzer no saca muy bien las versiones, las sacaremos a mano buscando en el source code la etiqueta <meta> que contiene la versión usada:

<div style="text-align:center"><img src="images/4.png" /></div>

Hay una web llamada PublicWWW que nos permite buscar determinado código en las webs, es decir podremos buscar webs que tengan una determinada versión de WordPress:

<div style="text-align:center"><img src="images/5.png" /></div>


Una vez descargadas todas las URLs tendremos el siguiente numero de webs para cada versión:

<div style="text-align:center"><img src="images/6.png" /></div>

Teniendo un total de 172.394 urls las cuales exportaremos a un csv:

<div style="text-align:center"><img src="images/7.png" /></div>



## Multi-Class Classification algorithms

Del mismo modo que la clasificación binaria (binary classification) implica predecir si algo es de una de dos clases (por ejemplo, "negro" o "blanco", "muerto" o "vivo", etc.), los problemas multiclase (Multi-class classification) implican clasificar algo en una de las N clases (por ejemplo, "rojo", "Blanco" o "azul", etc.)

Los ejemplos comunes incluyen la clasificación de imágenes (es un gato, perro, humano, etc.) o el reconocimiento de dígitos escritos a mano (clasificar una imagen de un número escrito a mano en un dígito de 0 a 9).
La librería scikit learn ofrece una serie de algoritmos para Multi-Class classification, algunos como:
-	K-nearest-neighbours (KNN).
-	Random Forest


## Dataset generation


Crearemos una función para el multiprocesado de URLS, sino será infinito este proceso.

Como esto es un programa I/O, es decir el cuello de botella se basará en lo que tarde en visitar esa página y no dependerá tanto del procesador usaremos el método de threading (https://realpython.com/python-concurrency/):

![Image of Yaktocat](images/10.png)

```python
def get_bytes(url):
    session = get_session()
    try:
        with session.get(url, verify=False, timeout=5) as response:
            if response.status_code == 200:
                bytess = len(response.content)
            elif response.status_code != 200:
                bytess = 0
    except:
        bytess = 0
    return bytess

def create_dataset(url):
    ...
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            bytess = list(executor.map(get_bytes, urlypath))
            for b in bytess:
                main_array.append(b)      
    ...

def create_dataset_multiple(urls):
    global count_iter 
    count_iter = -12
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        df = pd.concat(executor.map(create_dataset, urls))
    return df
```

```python
df = pd.read_csv('final.csv')
urls = df['URLs'].sample(n=100000) 
create_dataset_multiple(urls)
```

## Training process

Cargamos y separaramos nuestro dataset en train(70%) y test(30%):

```python
df = pd.read_csv('20000.csv')
X = df.iloc[:, 1:-1].values
y = df.iloc[:, -1].values

from sklearn.model_selection import train_test_split
# 70% training 30% test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
```

Una vez separado el dataset, entrenaremos a nuestro modelo.

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=10, criterion='entropy', random_state=42)
model.fit(X_train, y_train)
```

Veremos el accuracy:

```python
from sklearn.model_selection import cross_val_score

y_pred = model.predict(X_test)
from sklearn import metrics
print("Accuracy Random Forest:",metrics.accuracy_score(y_test, y_pred))
scores = cross_val_score(model, X_test, y_test, cv=5)
print("Accuracy Cross val score Random Forest: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))

```

Guardamos nuestro modelo:

```python
from sklearn.externals import joblib
joblib.dump(model, 'randomforestmodel.pkl') 
```

Hacemos las prediciones:

```python
# Creamos un dataframe en blanco
df = pd.DataFrame(columns=client)
create_dataset_to_predict("https://www.cloudways.com/blog/creating-custom-page-template-in-wordpress/")
X = df.iloc[:, 0:-1].values
model.predict(X)
```
