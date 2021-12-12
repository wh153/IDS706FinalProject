FROM continuumio/miniconda3:4.10.3-alpine

# copy files
COPY lambda_function.py /app/
COPY dash_app.py /app/
COPY forecast.csv /app/

# Use conda to install packages
RUN conda install --yes --freeze-installed -c conda-forge \
    pandas \
    numpy \
    boto3 \
    python-json-logger \
    flask \
    httpstan==4.6.1 \
    pystan==2.19.1.1 \
    dash \
    dash-html-components \
    dash-core-components \
    plotly \
    && conda clean -afy

RUN conda install --yes --freeze-installed -c conda-forge \
    prophet \
    && conda clean -afy \
    && find /opt/conda/ -follow -type f -name '*.a' -delete \
    && find /opt/conda/ -follow -type f -name '*.pyc' -delete \
    && find /opt/conda/ -follow -type f -name '*.js.map' -delete

# check important packages are installed properly
RUN echo "Check prophet is installed"
RUN python -c "from prophet import Prophet"

WORKDIR /app

EXPOSE 80
EXPOSE 8080

# entry point
ENTRYPOINT [ "python" ]
CMD [ "/app/dash_app.py" ]